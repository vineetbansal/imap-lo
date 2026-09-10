"""Generate pointing_file.csv (spin-axis RA/Dec per day) from L1C pset CDFs.

Replaces the hand-maintained config_files/pointing_file.csv with a file derived
from SPICE-computed geometry already carried in the L1C pset products, so the
quicklook pipeline and the SDC share one source of truth for attitude.

Geometry
--------
The L1C pset carries ``hae_longitude``/``hae_latitude`` -- the sky direction of
every (spin angle, look direction) bin, in HAE/ECLIPJ2000.  For a fixed look
direction the boresight sweeps a cone about the spin axis as the spacecraft
spins, so every sample satisfies ``v . n = cos(pivot_angle)`` for spin axis
``n``.  That is the equation of a plane, so the samples for one look direction
lie in a plane whose normal *is* the spin axis.  Fitting a plane per look
direction and averaging the normals recovers it exactly.

Do NOT try to average the boresight vectors directly: at the nominal 90 deg
pivot the boresight sweeps a great circle, the mean is ~0, and the result is
dominated by sampling asymmetry (it comes out near the anti-sun direction,
~177 deg away from the true axis).

Frames and conventions
----------------------
The pset is in ECLIPJ2000; the historical pointing_file.csv is in equatorial
J2000.  Output defaults to J2000 to stay drop-in compatible.

The value written is the axis averaged over the whole pointing.  The historical
file appears to hold an instantaneous value at the day boundary instead -- the
two differ by a stable ~0.6 deg, with this file's value sitting ~60% of the way
toward the next day's entry.  That is a convention difference, not an error.

Writing
-------
The output is merged, not replaced: only the days recomputed from the psets on
hand are (re)written, and every other YYYYDDD already in the file is carried
over verbatim.  So a run over a single day's pset updates that day and leaves
the rest of the file alone.

Usage
-----
    python scripts/generate_pointing_file.py \\
        --pset-dir input_l1c --out 3S5_l1b_ram_maps/config_files/pointing_file.csv
"""

import argparse
import datetime as dt
import glob
import os
from pathlib import Path

import numpy as np
import spiceypy
from spacepy import pycdf

_SPICE_DIR = Path(__file__).parent.parent / "input_SPICE"


def furnish_kernels() -> None:
    """Load the leap-second and planetary ephemeris kernels (Sun direction only)."""
    for rel in ("lsk/naif0012.tls", "spk/de440.bsp"):
        path = _SPICE_DIR / rel
        if not path.exists():
            raise FileNotFoundError(f"required SPICE kernel missing: {path}")
        spiceypy.furnsh(str(path))


def _bin_directions(cdf: pycdf.CDF) -> np.ndarray:
    """Return unit vectors of shape (n_spin, n_look, 3) in ECLIPJ2000.

    Handles both pset layouts seen in the archive: ``(1, 3600, 40)`` and the
    ESA-resolved ``(1, 7, 3600, 40)``.  The trailing two axes are always
    (spin angle, look direction); leading axes are collapsed and the first
    slice taken, since the pointing geometry is identical across them.
    """
    lon = np.asarray(cdf["hae_longitude"][...], dtype=float)
    lat = np.asarray(cdf["hae_latitude"][...], dtype=float)
    lon = np.deg2rad(lon.reshape(-1, *lon.shape[-2:])[0])
    lat = np.deg2rad(lat.reshape(-1, *lat.shape[-2:])[0])
    return np.stack(
        [np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1
    )


def spin_axis_eclipj2000(cdf: pycdf.CDF) -> np.ndarray:
    """Fit the spin axis as the mean plane-normal over look directions.

    The normal comes from the smallest eigenvector of each 3x3 covariance --
    equivalent to an SVD plane fit, but without materialising the (n_spin,
    n_spin) left-singular matrix that ``np.linalg.svd`` builds by default.
    """
    v = _bin_directions(cdf)
    normals = []
    for k in range(v.shape[1]):
        pts = v[:, k, :]
        pts = pts[np.isfinite(pts).all(axis=1)]
        if len(pts) < 10:
            continue
        centred = pts - pts.mean(axis=0)
        _, eigvec = np.linalg.eigh(centred.T @ centred)
        normals.append(eigvec[:, 0])          # smallest eigenvalue -> plane normal
    if not normals:
        raise ValueError("no usable look directions")

    n = np.asarray(normals)
    n *= np.sign(n @ n[0])[:, None]           # normals are sign-ambiguous; align them
    axis = n.mean(axis=0)
    return axis / np.linalg.norm(axis)


def sun_direction(when: dt.datetime) -> np.ndarray:
    """Return the ECLIPJ2000 unit vector toward the Sun at noon on *when*."""
    et = spiceypy.str2et(when.strftime("%Y-%m-%dT12:00:00"))
    sun, _ = spiceypy.spkpos("SUN", et, "ECLIPJ2000", "LT+S", "EARTH")
    return sun / np.linalg.norm(sun)


def orient_sunward(axis: np.ndarray, when: dt.datetime) -> np.ndarray:
    """Resolve the remaining global sign by pointing the axis sunward.

    A plane normal is defined only up to sign.  IMAP is a sun-pointing spinner,
    so the axis is always within a few degrees of the Sun.  Using cos(pivot)
    instead would be exact in principle but fails in practice: the pivot is
    ~90 deg for most pointings, making its cosine vanishingly small.
    """
    return axis if np.dot(axis, sun_direction(when)) > 0 else -axis


def sun_angle_deg(axis: np.ndarray, when: dt.datetime) -> float:
    """Angle in degrees between a spin axis and the Sun -- the sanity check on it."""
    cos = np.dot(axis, sun_direction(when))
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def to_ra_dec(vec: np.ndarray, frame: str) -> tuple[float, float]:
    """Convert an ECLIPJ2000 unit vector to (RA, Dec) in degrees in *frame*."""
    if frame.upper() == "J2000":
        vec = spiceypy.pxform("ECLIPJ2000", "J2000", 0.0) @ vec
    ra = np.rad2deg(np.arctan2(vec[1], vec[0])) % 360.0
    dec = np.rad2deg(np.arcsin(np.clip(vec[2], -1.0, 1.0)))
    return ra, dec


# Real pset versions are v001..v009 (with an optional .000N revision).  The
# archive also carries synthetic/test products at v963, v991 and v997.  A plain
# "highest version wins" rule prefers those, and on 2026-001 that put a
# repoint01261 test file (pivot exactly 90.000) into the output, 51.9 deg away
# from the real attitude.  Anything at or above this is treated as out of band.
#
# Rejecting them outright is wrong too.  2026-017 and 2026-018 carry a v997
# product and nothing else, yet their attitude is real: it lands on the trend set
# by the neighbouring days to within 0.05 deg.  Skipping them left those two days
# out of pointing_file.csv, which made l1b_to_spin.py drop the days entirely --
# about half of the pivot-90 map's 6.8% exposure deficit against the SDC L2.
#
# So an out-of-band product is used only where the day has no in-band
# alternative, and only if the axis it yields survives MAX_SUN_ANGLE_DEG.
TEST_VERSION_FLOOR = 900

# IMAP is a sun-pointing spinner.  Across the 159 in-band psets in input_l1c the
# recovered spin axis sits 3.31-3.96 deg from the Sun; the 2026-001 test product
# was 51.9 deg off.  Any threshold in between separates them; 10 deg leaves room
# for real off-pointing without letting a synthetic attitude through.
MAX_SUN_ANGLE_DEG = 10.0


def parse_version(name: str) -> tuple[int, int]:
    """Return (major, revision) from ``..._vNNN[.NNNN].cdf``; (-1, -1) if absent."""
    tail = name.rsplit("_v", 1)
    if len(tail) != 2:
        return (-1, -1)
    parts = tail[1].removesuffix(".cdf").split(".")
    try:
        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except ValueError:
        return (-1, -1)


def pset_files_by_day(pset_dir: Path, allow_test: bool = False) -> dict[int, tuple[str, bool]]:
    """Map YYYYDDD -> (best pset file, came_from_out_of_band) for that day.

    In-band products always win.  A day whose only products are out of band falls
    back to the best of those, flagged so the caller can sanity check the axis it
    yields before trusting it -- see TEST_VERSION_FLOOR.
    """
    in_band: dict[int, list[tuple[tuple[int, int], str]]] = {}
    out_of_band: dict[int, list[tuple[tuple[int, int], str]]] = {}
    for path in sorted(glob.glob(str(pset_dir / "*.cdf"))):
        name = os.path.basename(path)
        version = parse_version(name)
        stamp = name.split("_")[4].split("-")[0]
        yd = int(dt.datetime.strptime(stamp, "%Y%m%d").strftime("%Y%j"))
        bucket = in_band if (allow_test or version[0] < TEST_VERSION_FLOOR) else out_of_band
        bucket.setdefault(yd, []).append((version, path))

    chosen = {yd: (max(v)[1], False) for yd, v in in_band.items()}
    for yd, v in out_of_band.items():
        if yd not in chosen:
            chosen[yd] = (max(v)[1], True)
    return chosen


HEADER = "YYYYDDD,SPINRA,SPINDEC"


def read_existing(path: Path) -> dict[int, str]:
    """Map YYYYDDD -> the file's own line for it, so untouched days survive verbatim.

    Anything whose first field is not an integer day (the header, blank lines,
    comments) is dropped rather than guessed at; the header is rewritten below.
    """
    if not path.exists():
        return {}
    rows: dict[int, str] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            yd = int(line.split(",", 1)[0])
        except ValueError:
            continue
        rows[yd] = line
    return rows


def merge_into(path: Path, rows: list[tuple[int, float, float]]) -> list[int]:
    """Write *rows* into *path*, preserving existing days that *rows* does not cover.

    The file is rewritten in full -- there is no way to splice a line into a CSV
    in place -- but every day not recomputed keeps the exact text it had.
    Returns the days carried over.
    """
    merged = read_existing(path)
    kept = sorted(set(merged) - {yd for yd, _, _ in rows})
    for yd, ra, dec in rows:
        merged[yd] = f"{yd},{ra:.6f},{dec:.6f}"

    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as fh:
        fh.write(HEADER + "\n")
        for yd in sorted(merged):
            fh.write(merged[yd] + "\n")
    os.replace(tmp, path)
    return kept


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--pset-dir", type=Path, default=Path("input_l1c"))
    ap.add_argument("--out", type=Path,
                    default=Path("3S5_l1b_ram_maps/config_files/pointing_file.csv"))
    ap.add_argument("--frame", choices=("J2000", "ECLIPJ2000"), default="J2000",
                    help="J2000 (default) matches the historical pointing_file.csv")
    ap.add_argument("--allow-test-versions", action="store_true",
                    help=f"include products at v{TEST_VERSION_FLOOR}+ (synthetic/test)")
    args = ap.parse_args()

    furnish_kernels()
    by_day = pset_files_by_day(args.pset_dir, args.allow_test_versions)
    if not by_day:
        raise SystemExit(f"no pset CDFs found under {args.pset_dir}")

    rows, failed, recovered = [], [], []
    for yd, (path, out_of_band) in sorted(by_day.items()):
        name = os.path.basename(path)
        try:
            with pycdf.CDF(path) as cdf:
                axis = spin_axis_eclipj2000(cdf)
        except Exception as exc:                       # noqa: BLE001 - report and continue
            failed.append((yd, name, str(exc)[:60]))
            continue
        when = dt.datetime.strptime(str(yd), "%Y%j")
        axis = orient_sunward(axis, when)

        # An out-of-band product is the only source for this day, so its attitude
        # has to earn its place rather than be taken on trust.
        angle = sun_angle_deg(axis, when)
        if out_of_band and angle > MAX_SUN_ANGLE_DEG:
            failed.append((yd, name, f"out-of-band axis {angle:.1f} deg from Sun"))
            continue
        if out_of_band:
            recovered.append((yd, name, angle))

        ra, dec = to_ra_dec(axis, args.frame)
        rows.append((yd, ra, dec))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    kept = merge_into(args.out, rows)

    print(f"{args.out}: {len(rows)} days written [{rows[0][0]}..{rows[-1][0]}], "
          f"{len(kept)} kept from the existing file, frame={args.frame}")
    for yd, name, angle in recovered:
        print(f"  from out-of-band product (no in-band pset for this day, "
              f"axis {angle:.2f} deg from Sun): {yd} {name}")
    for yd, name, err in failed:
        print(f"  SKIPPED {yd} {name}: {err}")


if __name__ == "__main__":
    main()
