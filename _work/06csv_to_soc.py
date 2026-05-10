from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime


N_HISTOGRAM_BINS: int = 60
N_COLAT_BINS: int = 30
PIVOT_ANGLES: list[float] = [75, 90, 105]


def build_header(stem, hmin, hmax):
    type_map = {
        "cats": ("Total Counts", "counts"),
        "expo": ("Exposure Time", "exposure (s)"),
        "flux": ("Flux", "flux (1 / cm^2 s sr keV)"),
        "rate": ("Rate", "rate ( 1/s)"),
    }
    now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    h_title, desc = next(
        (v for k, v in type_map.items() if k in stem.lower()),
        ("Unknown", "unknown")
    )

    return f"""\
# 27:30x60:-5.0x-5.0:7x6:0:9
#
# {now}
#
# flux_translate
#
#  -s matrix
#
#  -0 dec (addresses incr. downwards)
#  -1 ra (addresses incr. left->right)
#
#  h_min={hmin:.8f} h_max={hmax:.8f} h_title='{h_title}'
#  min_0=-90 max_0=90 num_0=30 title_0='Dec (deg)'
#  min_1=0 max_1=360 num_1=60 title_1='R.A. (deg)'
#  desc="'{desc}'"
#  skyframe=ECLIPJ2000 posframe=J2000
#
#  chat=0 smearspread='0/0/0' calc='0/0/0'
#  frame_epoch=914561779.587 resp_class=lo_triple zaxis_ra_deg=+274.476346 zaxis_dec_deg=-22.782473
#  ram_ra_deg=+186.7725 ram_dec_deg=-3.2847 mtype_list='40' energy_list='21,41'
#  check_mt_list='40' check_species='20' rate_factor='1000' e_nominal='0.015'
#
#
#
#
#
# """.splitlines()


def process(map_dir: Path, output_dir: Path, pivot_angles: list[float] | None = None):

    output_dir.mkdir(parents=True, exist_ok=True)

    if pivot_angles is None:
        pivot_angles = PIVOT_ANGLES

    for pivot_angle in pivot_angles:
        for csv_file in Path(map_dir).glob(f"map_pivot-{pivot_angle}*.csv"):

            df = pd.read_csv(csv_file)

            data = df.to_numpy(dtype=float)
            assert data.shape == (30, 60)

            h_min = np.nanmin(data)
            h_max = np.nanmax(data)

            header = build_header(csv_file.stem, h_min, h_max)

            with open(output_dir / (csv_file.stem + ".txt"), "w") as f:
                f.write("\n".join(header) + "\n")
                for row in data:
                    f.write("\t".join(f"{val:.6e}" for val in row) + "\n")


if __name__ == "__main__":
    process(
        Path("output/maps"),
        Path("output/soc")
    )