"""Convert 3S5 or 3S7 ram-map CSVs into an IMAP-Lo L2 intensity-map CDF.

From 3S5 this produces the equivalent of the SDC's ``enansnbs`` product -- ENA
intensity with No Sputter and No BootStrap corrections. From 3S7 it produces
``enasbs``, the same intensity after the sputter and bootstrap corrections.
Which one is decided by the step folder --maps-dir is in. 3S8
(compton-getting) is not handled.

The CDF schema is cloned from a reference SDC file rather than hand-written, so
every global attribute, variable attribute, data type and dimension matches by
construction.  Only the science arrays and the time coverage are substituted.

Usage
-----
    python scripts/maps_to_l2_cdf.py \\
        --maps-dir 3S5_l1b_ram_maps/outdir/pivot_90/maps \\
        --template /path/to/imap_lo_l2_l090-enansnbs-...-6mo_20251125_v001.cdf \\
        --out-dir  3S5_l1b_ram_maps/outdir/pivot_90/cdf

Pass ``--maps-dir 3S7_l1b_sputterbootstrap_ram/outdir/pivot_90/maps`` for the
enasbs product; the same template works for both.
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

_SQRT = np.sqrt
_3S5 = "3S5_l1b_ram_maps"
_3S7 = "3S7_l1b_sputterbootstrap_ram"

# L2 variable <- (step folder, map file name for an ESA step, transform).
#
# The 3S5 entries were verified against a reference SDC file by taking the
# ratio candidate/reference over all valid pixels; each pairing reproduces the
# reference exactly (median ratio 1.0000, IQR 1.000-1.000).
#
# Two are not what the 3S5 label_map naming suggests: the statistical
# uncertainties are sqrt of the *variance* maps, not the "unc" maps, and
# `bfunc` -- despite the name -- is the background *systematic* error.
#
# 3S7 corrects only the ENA intensity and writes no background maps, so both
# products take the background from 3S5. The SDC does the same: its enasbs
# bg_intensity is identical to its enansnbs one.
_BACKGROUND = {
    "bg_intensity": (_3S5, "map_bflux_esa{esa}.csv", None),
    "bg_intensity_stat_uncert": (_3S5, "map_bfvar_esa{esa}.csv", _SQRT),
    "bg_intensity_sys_err": (_3S5, "map_bfunc_esa{esa}.csv", None),
}

# Each pipeline step a maps directory can come from, by its folder name: the
# SDC product its maps are the equivalent of, the step whose
# map_l1b_manifest_esa*.csv give the time coverage, and where each variable is
# read from. 3S7 is built from the 3S5 maps and writes no manifest of its own.
STEPS = {
    _3S5: {
        "descriptor": "enansnbs-h-sf-nsp-ram-hae-6deg-6mo",
        "manifests": _3S5,
        "sources": {
            "ena_intensity": (_3S5, "map_flux_esa{esa}.csv", None),
            "ena_intensity_stat_uncert": (_3S5, "map_fvar_esa{esa}.csv", _SQRT),
            "ena_intensity_sys_err": (_3S5, "map_fser_esa{esa}.csv", None),
            "ena_intensity_sys_err_minus": (_3S5, "map_fsel_esa{esa}.csv", None),
            "ena_intensity_sys_err_plus": (_3S5, "map_fseu_esa{esa}.csv", None),
            "exposure_factor": (_3S5, "map_expo_esa{esa}.csv", None),
            **_BACKGROUND,
        },
    },
    # Sputter then bootstrap corrected, from correction_v4.py. Its "sput"
    # maps are the sputter correction alone, an intermediate step the SDC
    # does not publish a product for.
    _3S7: {
        "descriptor": "enasbs-h-sf-nsp-ram-hae-6deg-6mo",
        "manifests": _3S5,
        "sources": {
            "ena_intensity": (_3S7, "map_flux_{esa}_Hy_boot_cor.csv", None),
            "ena_intensity_stat_uncert": (_3S7, "map_flux_{esa}_Hy_boot_var.csv", _SQRT),
            "ena_intensity_sys_err": (_3S7, "map_flux_{esa}_Hy_boot_unc.csv", None),
            "ena_intensity_sys_err_minus": (_3S7, "map_flux_{esa}_Hy_boot_unl.csv", None),
            "ena_intensity_sys_err_plus": (_3S7, "map_flux_{esa}_Hy_boot_unu.csv", None),
            "exposure_factor": (_3S7, "map_expo_esa{esa}.csv", None),
            **_BACKGROUND,
        },
    },
}

# No 3S5 equivalent exists; the reference SDC file leaves these fully filled too.
FILLED_FLOAT = ("solid_angle", "obs_date_range")
FILLED_INT = ("obs_date",)


def locate(maps_dir: Path) -> tuple[str, Path, Path]:
    """Split a maps directory into its pipeline step and where that sits.

    Returns the step folder name, the directory holding the step folders, and
    the path below the step folder (e.g. outdir/pivot_90/maps), so the same
    directory can be found in another step: ``root / step / below``.
    """
    parts = maps_dir.parts
    for i, part in enumerate(parts):
        if part in STEPS:
            return part, Path(*parts[:i]), Path(*parts[i + 1:])
    raise ValueError(
        f"{maps_dir} is not inside any of the known pipeline steps: "
        + ", ".join(STEPS)
    )


def read_map(path: Path) -> np.ndarray:
    """Read one map CSV as a (N_LON, N_LAT) array.

    On disk each file is a bare (30, 60) grid -- 30 latitude rows by 60
    longitude columns. Most are written by
    ``pd.DataFrame(arr).to_csv(index=False)``, so they have a throwaway header
    row of the column labels 0..59; 3S7's exposure maps are written by
    ``np.savetxt`` and have none. The row count tells the two apart.

    3S5's map_SCFrame_V2.py fills these with ``theta = 90 + dec;
    jmap = int(theta/6)`` and ``imap = int(ra/6)``, so row 0 is latitude -87
    and column 0 is longitude 3 -- already the L2 coordinate order.  Only a
    transpose to (longitude, latitude) is needed, no flips. 3S7 reads the 3S5
    maps and writes its own in the same order.
    """
    arr = pd.read_csv(path, header=None).to_numpy(dtype=float)
    if arr.shape == (N_LAT + 1, N_LON):
        arr = arr[1:]
    if arr.shape != (N_LAT, N_LON):
        raise ValueError(f"{path}: expected {(N_LAT, N_LON)}, got {arr.shape}")
    return arr.T


def stack_quantity(directory: Path, filename: str) -> np.ndarray:
    """Stack ESA levels 1..7 into the L2 (1, energy, longitude, latitude) shape."""
    return np.stack([
        read_map(directory / filename.format(esa=e)) for e in range(1, N_ESA + 1)
    ])[None]


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
    step, root, below = locate(maps_dir)
    config = STEPS[step]
    start, span_ns, parents = time_coverage(root / config["manifests"] / below)

    data = {}
    for name, (source, filename, transform) in config["sources"].items():
        arr = stack_quantity(root / source / below, filename)
        data[name] = transform(arr) if transform else arr

    # Unobserved pixels carry no exposure; the SDC product marks those FILLVAL
    # rather than zero (its ena_intensity is ~55% fill). exposure_factor itself
    # keeps its zeros, matching the reference (0 fill, 6916 zeros).
    unobserved = data["exposure_factor"] <= 0
    for name in data:
        if name != "exposure_factor":
            data[name] = np.where(unobserved, FILL_F, data[name])

    descriptor = f"l{pivot:03d}-{config['descriptor']}"
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
        out.attrs["Generated_by"] = f"IMAP-Lo quicklook pipeline ({step})"
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
