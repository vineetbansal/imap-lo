import pandas as pd
import numpy as np
from pathlib import Path
from spacepy import pycdf


def process(input_cdf: Path, output_dir: Path):
    cdf = pycdf.CDF(str(input_cdf))
    output_dir.mkdir(exist_ok=True)

    for esa in range(7):

        data = {}
        for var in ('disc_tof0_rates', 'disc_tof1_rates', 'disc_tof2_rates',
                    'disc_tof3_rates', 'epoch', 'esa_mode', 'esa_step', 'esa_step_label',
                    'exposure_time_60deg', 'exposure_time_6deg', 'pos0_rates', 'pos1_rates',
                    'pos2_rates', 'pos3_rates', 'silver_triple_rates', 'spin_bin_6',
                    'spin_bin_60', 'spin_cycle', 'start_a_rates', 'start_c_rates',
                    'stop_b0_rates', 'stop_b3_rates', 'tof0_rates', 'tof0_tof1_rates',
                    'tof0_tof2_rates', 'tof1_rates', 'tof1_tof2_rates', 'tof2_rates',
                    'tof3_rates'):

            if len(np.shape(cdf[var])) == 1:
                d = cdf[var][:]
            elif len(np.shape(cdf[var])) == 2:
                d = cdf[var][:, esa]
            else:
                d = cdf[var][:, esa, :]
            data[var] = d

        for k in data:
            d = pd.DataFrame(data[k])
            d.to_csv(f"{output_dir}/{input_cdf.stem}_{k}_{esa+1}.csv", index=False)


if __name__ == "__main__":
    process(
        Path("/media/vineetb/T7/imap/lo/l1b/2026/04/imap_lo_l1b_monitorrates_20260413-repoint00217_v002.cdf"),
        Path("output")
    )