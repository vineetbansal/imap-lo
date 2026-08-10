from pathlib import Path
import numpy as np
import pandas as pd

nra    = 60
ncolat = 30

PIVOTS = [75, 90, 105]
ESAS   = range(1, 8)

# ----------------------------------------------------------------------
# Mask tuning by pivot angle and ESA
# Key is (pivot_angle, esa_step)
# ----------------------------------------------------------------------

spin_centers = 3.0 + 6.0 * np.arange(ncolat)
spinangle_map_deg = np.tile(spin_centers[:, None], (1, nra))

for pp in PIVOTS:

    ref_mask_dir = Path(f"../3S5_l1b_ram_maps/outdir/pivot_{pp}/masked_maps")
    work_dir_hydrogen = Path(f"./outdir/pivot_{pp}/maps")
    mask_dir = Path(f"./outdir/pivot_{pp}/masked_maps")
    mask_dir.mkdir(parents=True, exist_ok=True)

    for tar_esa in ESAS:

#        isn_mask = np.loadtxt(
#            ref_mask_dir / f"isn_mask_ESA{tar_esa}.csv",
#            delimiter=","
#        )
        filename = ref_mask_dir / f"isn_mask_ESA{tar_esa}.csv"
        df = pd.read_csv(filename)
        isn_mask = df.to_numpy()

        for tt in [
            "boot_cor", "boot_unc",  "boot_unl",  "boot_unu", "boot_var",
            "sput_cor", "sput_unc", "sput_unl",  "sput_unu", "sput_var"
        ]:

#            map_data = np.loadtxt(
#                work_dir_hydrogen / f"map_flux_{tar_esa}_Hy_{tt}.csv",
#                delimiter=",",
#                skiprows=1,
#            )
            filename = work_dir_hydrogen / f"map_flux_{tar_esa}_Hy_{tt}.csv"
            df = pd.read_csv(filename)
            map_data = df.to_numpy()

            if map_data.shape != isn_mask.shape:
                raise ValueError(
                    f"pivot {pp}, ESA{tar_esa}, {tt}: map shape {map_data.shape} "
                    f"does not match mask shape {isn_mask.shape}"
                )

            map_masked = np.where(isn_mask, np.nan, map_data)

           # np.savetxt(
           #     mask_dir / f"map_flux_{tar_esa}_Hy_{tt}.csv",
           #     map_masked,
           #     delimiter=",",
           #     fmt="%.6e",
           # )

            map_masked = pd.DataFrame(map_masked)
            map_masked.to_csv(
                mask_dir / f"map_flux_{tar_esa}_Hy_{tt}.csv",
                index=False
            )