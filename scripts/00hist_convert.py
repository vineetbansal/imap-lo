import pandas as pd
import numpy as np
from pathlib import Path
from spacepy import pycdf


def process(input_cdf: Path, output_dir: Path):

    cdf = pycdf.CDF(str(input_cdf))
    output_dir.mkdir(exist_ok=True)

    for esa in range(7):

        data = {}
        for var in ('epoch','esa_mode','exposure_time_6deg','h_counts','h_rates','o_counts','o_rates','spin_bin_6','spin_cycle'):
            if len(np.shape(cdf[var])) == 1:
                d = cdf[var][:]
            elif len(np.shape(cdf[var])) == 2:
                d = cdf[var][:,esa]
            else:
                d = cdf[var][:, esa, :]
            data[var] = d

        for k in data:
            d = pd.DataFrame(data[k])
            d.to_csv(f"{output_dir}/{input_cdf.stem}_{k}_{esa+1}.csv", index=False)


if __name__ == "__main__":
    process(
        Path("/media/vineetb/T7/imap/lo/l1b/2026/04/imap_lo_l1b_histrates_20260413-repoint00217_v002.cdf"),
        Path("output")
    )