#!/usr/bin/env python3
"""Generate pointing_file.csv (YYYYDDD, SPINRA, SPINDEC) from SPICE CK kernels.

For each day in the requested range, samples the IMAP spacecraft spin axis
(+Z of IMAP_SPACECRAFT in J2000) at hourly intervals and writes the daily
mean RA/Dec to a CSV file.

Usage:
    python generate_pointing_file.py [--start YYYYDDD] [--end YYYYDDD] [--out FILE]

Defaults to the range 2025250–2026365 and writes to
  config_files/pointing_file.csv  (relative to this script's directory).
"""

import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import spiceypy as spice
from imap_processing.spice.geometry import SpiceFrame
from imap_processing.spice.pointing_frame import _mean_spin_axis

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

T7 = Path("/media/vineetb/T7/imap/spice")
SCRIPTS_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Fixed kernels (always loaded)
# ---------------------------------------------------------------------------
FIXED_KERNELS = [
    T7 / "lsk/naif0012.tls",
    T7 / "sclk/imap_sclk_0162.tsc",  # latest SCLK
    T7 / "fk/imap_130.tf",
    T7 / "fk/imap_science_120.tf",
    T7 / "spk/de440.bsp",             # planetary ephemeris
]

# SPK priority: higher = preferred
_SPK_PRIORITY = {"recon": 3, "pred": 2, "nom": 1}


def _spk_priority(path: Path) -> int:
    name = path.name
    for key, val in _SPK_PRIORITY.items():
        if key in name:
            return val
    return 0


def _version(path: Path) -> int:
    """Extract trailing version number from filename (e.g. _v02 -> 2)."""
    stem = path.stem
    parts = stem.split("_v")
    try:
        return int(parts[-1])
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Build coverage indices
# ---------------------------------------------------------------------------

def build_ck_index() -> list[tuple[float, float, int, Path]]:
    """Return list of (start_et, end_et, version, path) for all IMAP_SPACECRAFT CKs."""
    spice.furnsh(str(T7 / "lsk/naif0012.tls"))
    spice.furnsh(str(T7 / "sclk/imap_sclk_0162.tsc"))

    entries = []
    # imap_* CKs contain body -43000 (IMAP_SPACECRAFT)
    for ck in sorted((T7 / "ck").glob("imap_[0-9]*.ah.bc")):
        try:
            ids = spice.ckobj(str(ck))
            if -43000 not in list(ids):
                continue
            cov = spice.ckcov(str(ck), -43000, False, "INTERVAL", 0.0, "TDB")
            for i in range(spice.wncard(cov)):
                s, e = spice.wnfetd(cov, i)
                entries.append((s, e, _version(ck), ck))
        except Exception:
            pass

    spice.kclear()
    return entries


def build_spk_index() -> list[tuple[float, float, int, int, Path]]:
    """Return list of (start_et, end_et, priority, version, path) for IMAP SPKs."""
    spice.furnsh(str(T7 / "lsk/naif0012.tls"))

    entries = []
    for spk in sorted((T7 / "spk").glob("imap_*.bsp")):
        try:
            ids = spice.spkobj(str(spk))
            if -43 not in list(ids):
                continue
            cov = spice.spkcov(str(spk), -43)
            for i in range(spice.wncard(cov)):
                s, e = spice.wnfetd(cov, i)
                entries.append((s, e, _spk_priority(spk), _version(spk), spk))
        except Exception:
            pass

    spice.kclear()
    return entries


def best_kernel_for_et(
    et: float, index: list[tuple]
) -> Path | None:
    """Return the highest-priority kernel covering et, or None."""
    covering = [e for e in index if e[0] <= et <= e[1]]
    if not covering:
        return None
    # sort by all priority fields (all elements after start/end), descending
    covering.sort(key=lambda e: e[2:], reverse=True)
    return covering[0][-1]


# ---------------------------------------------------------------------------
# Spin-axis computation for one day
# ---------------------------------------------------------------------------

def spin_axis_for_day(date: datetime, ck: Path, spk: Path) -> tuple[float, float] | None:
    """Return (mean_RA_deg, mean_Dec_deg) of the spin axis over the day, or None."""
    for k in [str(spk), str(ck)]:
        spice.furnsh(k)

    et_times = np.array([
        spice.str2et(
            date.replace(hour=h, minute=30, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        )
        for h in range(24)
    ])

    try:
        mean_vec = _mean_spin_axis(et_times, frame=SpiceFrame.J2000)
    except Exception as e:
        result = None
    else:
        _, ra_rad, dec_rad = spice.recrad(mean_vec)
        result = np.degrees(ra_rad), np.degrees(dec_rad)

    spice.unload(str(ck))
    spice.unload(str(spk))

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def yyyyddd_to_date(yyyyddd: int) -> datetime:
    return datetime.strptime(str(yyyyddd), "%Y%j")


def date_to_yyyyddd(date: datetime) -> int:
    return int(date.strftime("%Y%j"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=int, default=2025281, metavar="YYYYDDD")
    p.add_argument("--end",   type=int, default=2025282, metavar="YYYYDDD")
    p.add_argument(
        "--out",
        type=Path,
        default=SCRIPTS_DIR / "pointing_file.csv",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    log.info("Loading fixed kernels")
    for k in FIXED_KERNELS:
        spice.furnsh(str(k))

    log.info("Building CK coverage index")
    ck_index = build_ck_index()
    log.info("Building SPK coverage index")
    spk_index = build_spk_index()

    # Reload fixed kernels (build_*_index clears the pool)
    for k in FIXED_KERNELS:
        spice.furnsh(str(k))

    start_date = yyyyddd_to_date(args.start)
    end_date   = yyyyddd_to_date(args.end)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    skipped = []

    date = start_date
    while date <= end_date:
        yyyyddd = date_to_yyyyddd(date)
        et_noon = spice.str2et(date.strftime("%Y-%m-%dT12:00:00"))

        ck  = best_kernel_for_et(et_noon, ck_index)
        spk = best_kernel_for_et(et_noon, spk_index)

        if ck is None or spk is None:
            log.warning("No CK=%s or SPK=%s for %d — skipping", ck, spk, yyyyddd)
            skipped.append(yyyyddd)
            date += timedelta(days=1)
            continue

        result = spin_axis_for_day(date, ck, spk)
        if result is None:
            log.warning("No valid samples for %d — skipping", yyyyddd)
            skipped.append(yyyyddd)
        else:
            ra, dec = result
            rows.append((yyyyddd, ra, dec))
            log.info("%d  SPINRA=%.6f  SPINDEC=%.6f  ck=%s", yyyyddd, ra, dec, ck.name)

        date += timedelta(days=1)

    spice.kclear()

    with open(args.out, "w") as f:
        f.write("YYYYDDD,SPINRA,SPINDEC\n")
        for yyyyddd, ra, dec in rows:
            f.write(f"{yyyyddd},{ra:.9f},{dec:.9f}\n")

    log.info("Wrote %d rows to %s", len(rows), args.out)
    if skipped:
        log.warning("Skipped %d days: %s", len(skipped), skipped)


if __name__ == "__main__":
    main()
