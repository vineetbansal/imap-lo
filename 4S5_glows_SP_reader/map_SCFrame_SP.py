#!/usr/bin/python

import numpy as np
import pandas as pd
import os
from pathlib import Path

# --------------------------------------------------
# Map geometry
# --------------------------------------------------

deg = 6.0

nra = 60
ncolat = 30

# --------------------------------------------------
# Process pivot angles
# --------------------------------------------------

for pp in [75, 90, 105]:

    print(f"\nMaking Survival Probability Maps for Pivot {pp}")

    work_dir = f'./outdir_glows/pivot_{pp}/daily'
    map_dir  = f'./outdir_glows/pivot_{pp}/maps'

    os.makedirs(map_dir, exist_ok=True)

    data_dir = Path(work_dir)

    # --------------------------------------------------
    # Loop through ESA steps
    # --------------------------------------------------

    for esa in range(1, 8):

        print(f"ESA Step {esa}")

        # weighted sum of SP
        sp_sum_map = np.zeros((ncolat, nra))

        # total exposure
        exposure_map = np.zeros((ncolat, nra))

        # --------------------------------------------------
        # Read all daily files for this ESA step
        # --------------------------------------------------

        for filepath in data_dir.glob(f'*esa{esa}.csv'):

            print(filepath.name)

            df = pd.read_csv(filepath)

            ra   = df['ra'].values
            dec  = df['dec'].values
            expo = df['expo'].values

            sp   = df['survival_probability'].values

            # --------------------------------------------------
            # Bin into sky map
            # --------------------------------------------------

            for ia in range(len(ra)):

                theta = 90.0 + dec[ia]

                imap = int(ra[ia] / deg)
                if imap == 60:
                    imap = 0

                jmap = int(theta / deg)
                if jmap == 30:
                    jmap = 0

                # exposure-weighted accumulation
                sp_sum_map[jmap, imap] += sp[ia] * expo[ia]

                exposure_map[jmap, imap] += expo[ia]

        # --------------------------------------------------
        # Final weighted average map
        # --------------------------------------------------

        sp_map = np.zeros((ncolat, nra))

        good = exposure_map > 0

        sp_map[good] = (
            sp_sum_map[good] /
            exposure_map[good]
        )

        # --------------------------------------------------
        # Save outputs
        # --------------------------------------------------

        pd.DataFrame(sp_map).to_csv(
            f'{map_dir}/map_survival_probability_esa{esa}.csv',
            index=False
        )

        pd.DataFrame(exposure_map).to_csv(
            f'{map_dir}/map_exposure_esa{esa}.csv',
            index=False
        )

print("\nDone.")
