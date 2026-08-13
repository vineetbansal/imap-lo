"""Convert 3S5 ram-map CSVs into an IMAP-Lo L2 intensity-map CDF.

Produces the equivalent of the SDC's ``enansnbs`` product -- ENA intensity with
No Sputter and No BootStrap corrections -- which is exactly what 3S5 emits,
before 3S7 (sputter/bootstrap) and 3S8 (compton-getting) run.

The CDF schema is cloned from a reference SDC file rather than hand-written, so
every global attribute, variable attribute, data type and dimension matches by
construction.  Only the science arrays and the time coverage are substituted.

Usage
-----
    python scripts/maps_to_l2_cdf.py \\
        --maps-dir 3S5_l1b_ram_maps/outdir/pivot_90/maps \\
        --template /path/to/imap_lo_l2_l090-enansnbs-...-6mo_20251125_v001.cdf \\
        --out-dir  3S5_l1b_ram_maps/outdir/pivot_90/cdf
"""

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from spacepy import pycdf

N_ESA = 7
N_LON = 60
N_LAT = 30
FILL_F = -1e31
FILL_I = -9223372036854775808

# L2 variable <- (3S5 map quantity, transform).
#
# Every entry was verified against a reference SDC file by taking the ratio
# candidate/reference over all valid pixels; each pairing below reproduces the
# reference exactly (median ratio 1.0000, IQR 1.000-1.000).
#
# Two are not what the 3S5 label_map naming suggests: the statistical
# uncertainties are sqrt of the *variance* maps, not the "unc" maps, and
# `bfunc` -- despite the name -- is the background *systematic* error.
_SQRT = np.sqrt
VAR_SOURCES = {
    "ena_intensity": ("flux", None),
    "ena_intensity_stat_uncert": ("fvar", _SQRT),
    "ena_intensity_sys_err": ("fser", None),
    "ena_intensity_sys_err_minus": ("fsel", None),
    "ena_intensity_sys_err_plus": ("fseu", None),
    "bg_intensity": ("bflux", None),
    "bg_intensity_stat_uncert": ("bfvar", _SQRT),
    "bg_intensity_sys_err": ("bfunc", None),
    "exposure_factor": ("expo", None),
}

# Intensity variables are FILLVAL wherever there is no exposure; exposure_factor
# itself keeps its zeros, matching the reference (0 fill, 6916 zeros).
MASKED = tuple(k for k in VAR_SOURCES if k != "exposure_factor")

# No 3S5 equivalent exists; the reference SDC file leaves these fully filled too.
FILLED_FLOAT = ("solid_angle", "obs_date_range")
FILLED_INT = ("obs_date",)


def read_map(maps_dir: Path, quantity: str, esa: int) -> np.ndarray:
    """Read one map CSV as a (N_LON, N_LAT) array.

    On disk each file is a bare (30, 60) grid -- 30 latitude rows by 60
    longitude columns -- written by ``pd.DataFrame(arr).to_csv(index=False)``,
    so the header row is the throwaway column labels 0..59.

    3S5's map_SCFrame_V2.py fills these with ``theta = 90 + dec;
    jmap = int(theta/6)`` and ``imap = int(ra/6)``, so row 0 is latitude -87
    and column 0 is longitude 3 -- already the L2 coordinate order.  Only a
    transpose to (longitude, latitude) is needed, no flips.
    """
    path = maps_dir / f"map_{quantity}_esa{esa}.csv"
    arr = pd.read_csv(path).to_numpy(dtype=float)
    if arr.shape != (N_LAT, N_LON):
        raise ValueError(f"{path}: expected {(N_LAT, N_LON)}, got {arr.shape}")
    return arr.T


def stack_quantity(maps_dir: Path, quantity: str) -> np.ndarray:
    """Stack ESA levels 1..7 into the L2 (1, energy, longitude, latitude) shape."""
    return np.stack([read_map(maps_dir, quantity, e) for e in range(1, N_ESA + 1)])[None]


def time_coverage(maps_dir: Path) -> tuple[dt.datetime, int, list[str]]:
    """Derive epoch, span in nanoseconds, and parent filenames from the manifests.

    Falls back to a zero-length span if no manifest is present (older runs did
    not write one).
    """
    frames = [pd.read_csv(p) for p in sorted(maps_dir.glob("map_l1b_manifest_esa*.csv"))]
    if not frames:
        return dt.datetime(2000, 1, 1), 0, []

    man = pd.concat(frames, ignore_index=True)
    days = sorted({str(d) for d in man["date_yyyymmdd"]})
    start = dt.datetime.strptime(days[0], "%Y%m%d")
    end = dt.datetime.strptime(days[-1], "%Y%m%d") + dt.timedelta(days=1)
    parents = sorted({str(f) for f in man["l1b_filename"]})
    return start, int((end - start).total_seconds() * 1e9), parents


def build(maps_dir: Path, template_path: Path, out_dir: Path, pivot: int,
          version: str = "001") -> Path:
    start, span_ns, parents = time_coverage(maps_dir)

    data = {}
    for name, (quantity, transform) in VAR_SOURCES.items():
        arr = stack_quantity(maps_dir, quantity)
        data[name] = transform(arr) if transform else arr

    # Unobserved pixels carry no exposure; the SDC product marks those FILLVAL
    # rather than zero (its ena_intensity is ~55% fill).
    unobserved = data["exposure_factor"] <= 0
    for name in MASKED:
        data[name] = np.where(unobserved, FILL_F, data[name])

    descriptor = f"l{pivot:03d}-enansnbs-h-sf-nsp-ram-hae-6deg-6mo"
    stem = f"imap_lo_l2_{descriptor}_{start:%Y%m%d}_v{version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stem}.cdf"
    if out_path.exists():
        out_path.unlink()

    with pycdf.CDF(str(template_path)) as tpl, pycdf.CDF(str(out_path), "") as out:
        out.attrs.clone(tpl.attrs)
        out.attrs["Logical_source"] = f"imap_lo_l2_{descriptor}"
        out.attrs["Logical_file_id"] = stem
        out.attrs["Data_type"] = (
            f"L2_{descriptor}>Level-2 Intensity Map for Lo"
        )
        out.attrs["Data_version"] = version
        out.attrs["Generated_by"] = "IMAP-Lo quicklook pipeline (3S5 ram maps)"
        out.attrs["Generation_date"] = f"{dt.date.today():%Y%m%d}"
        if parents:
            out.attrs["Parents"] = parents

        for name in tpl:
            substitute = name in data or name in FILLED_FLOAT or name in FILLED_INT
            # Coordinates, labels and deltas are instrument constants -- carry
            # them over from the template verbatim.
            out.clone(tpl[name], name, data=not substitute)

            if name in data:
                out[name] = data[name]
            elif name in FILLED_FLOAT:
                out[name] = np.full(tpl[name].shape, FILL_F)
            elif name in FILLED_INT:
                out[name] = np.full(tpl[name].shape, FILL_I, dtype=np.int64)

        out["epoch"] = [start]
        out["epoch_delta"] = [span_ns]
        out["epoch_delta_minus"] = [0]

    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maps-dir", required=True, type=Path,
                    help="e.g. 3S5_l1b_ram_maps/outdir/pivot_90/maps")
    ap.add_argument("--template", required=True, type=Path,
                    help="reference SDC L2 CDF to clone the schema from")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="default: <maps-dir>/../cdf")
    ap.add_argument("--pivot", type=int, default=None,
                    help="default: parsed from the pivot_NN directory name")
    ap.add_argument("--version", default="001")
    args = ap.parse_args()

    pivot = args.pivot
    if pivot is None:
        for part in args.maps_dir.parts:
            if part.startswith("pivot_"):
                pivot = int(part.split("_")[1])
        if pivot is None:
            ap.error("--pivot not given and no pivot_NN component in --maps-dir")

    out_dir = args.out_dir or args.maps_dir.parent / "cdf"
    path = build(args.maps_dir, args.template, out_dir, pivot, args.version)
    print(path)


if __name__ == "__main__":
    main()
