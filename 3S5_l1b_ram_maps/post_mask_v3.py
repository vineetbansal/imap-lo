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

h_thresh_by_pp_esa = {
    (75, 1): 0.015, (75, 2): 0.015, (75, 3): 0.015, (75, 4): 0.008,
    (75, 5): 0.02, (75, 6): 1.0, (75, 7): 1.0,

    (90, 1): 0.01, (90, 2): 0.01, (90, 3): 0.005, (90, 4): 0.005,
    (90, 5): 0.1, (90, 6): 1.0, (90, 7): 1.0,

    (105, 1): 0.01, (105, 2): 0.005, (105, 3): 0.001, (105, 4): 0.005,
    (105, 5): 0.15, (105, 6): 1.0, (105, 7): 1.0,
}

angular_width_by_pp_esa = {
    (75, 1): 80.0, (75, 2): 70.0, (75, 3): 70.0, (75, 4): 70.0,
    (75, 5): 25.0, (75, 6): 35.0, (75, 7): 35.0,

    (90, 1): 80.0, (90, 2): 70.0, (90, 3): 65.0, (90, 4): 50.0,
    (90, 5): 45.0, (90, 6): 35.0, (90, 7): 35.0,

    (105, 1): 80.0, (105, 2): 60.0, (105, 3): 60.0, (105, 4): 40.0,
    (105, 5): 35.0, (105, 6): 35.0, (105, 7): 35.0,
}

outlier_percentile_by_pp_esa = {
    (75, 1): 99.999, (75, 2): 99.999, (75, 3): 99.999, (75, 4): 99.999,
    (75, 5): 96.999, (75, 6): 99.999, (75, 7): 99.999,

    (90, 1): 99.999, (90, 2): 99.999, (90, 3): 99.999, (90, 4): 99.999,
    (90, 5): 99.999, (90, 6): 99.999, (90, 7): 99.999,

    (105, 1): 99.999, (105, 2): 99.999, (105, 3): 99.999, (105, 4): 99.999,
    (105, 5): 99.999, (105, 6): 99.999, (105, 7): 99.999,
}


def circular_distance_deg(a, b):
    return np.abs((a - b + 180.0) % 360.0 - 180.0)


def make_isn_mask(h_map, angle_map_deg, h_thresh_frac=0.25, angular_max=50.0):
    hmax = np.nanmax(h_map)

    if not np.isfinite(hmax) or hmax <= 0:
        return np.zeros_like(h_map, dtype=bool)

    h_bright = h_map >= h_thresh_frac * hmax

    dang = circular_distance_deg(angle_map_deg, 90.0)
    near_peak = dang <= angular_max

    return h_bright & near_peak

def make_high_outlier_mask(h_map, percentile=99.5):
    vals = h_map[np.isfinite(h_map)]

    if vals.size == 0:
        return np.zeros_like(h_map, dtype=bool)

    cutoff = np.percentile(vals, percentile)

    return h_map > cutoff

spin_centers = 3.0 + 6.0 * np.arange(ncolat)
spinangle_map_deg = np.tile(spin_centers[:, None], (1, nra))

for pp in PIVOTS:

    work_dir_hydrogen = Path(f"./outdir/pivot_{pp}/maps")
    mask_dir = Path(f"./outdir/pivot_{pp}/masked_maps")
    mask_dir.mkdir(parents=True, exist_ok=True)

    for tar_esa in ESAS:

        key = (pp, tar_esa)

        h_thresh_frac = h_thresh_by_pp_esa[key]
        angular_max   = angular_width_by_pp_esa[key]

#        h_map = np.loadtxt(
#            work_dir_hydrogen / f"map_flux_esa{tar_esa}.csv",
#            delimiter=",",
#            skiprows=1,
#        )
        filename = work_dir_hydrogen / f"map_flux_esa{tar_esa}.csv"
        df = pd.read_csv(filename)
        h_map = df.to_numpy()

        if h_map.shape != spinangle_map_deg.shape:
            raise ValueError(
                f"pivot {pp}, ESA{tar_esa}: h_map shape {h_map.shape} "
                f"does not match angle map shape {spinangle_map_deg.shape}"
            )

        isn_mask = make_isn_mask(
            h_map=h_map,
            angle_map_deg=spinangle_map_deg,
            h_thresh_frac=h_thresh_frac,
            angular_max=angular_max,
        )

        outlier_mask = make_high_outlier_mask(
            h_map=h_map,
            percentile=outlier_percentile_by_pp_esa[key],
        )

        total_mask = isn_mask | outlier_mask

#        np.savetxt(
#            mask_dir / f"isn_mask_ESA{tar_esa}.csv",
#            total_mask.astype(int),
#            delimiter=",",
#            fmt="%d",
#        )

        total_mask = pd.DataFrame(total_mask)
        total_mask.to_csv(
                mask_dir / f"isn_mask_ESA{tar_esa}.csv",
                index=False
            )

        h_masked = np.where(total_mask, np.nan, h_map)

#        np.savetxt(
#            mask_dir / f"map_flux_esa{tar_esa}.csv",
#            h_masked,
#            delimiter=",",
#            fmt="%.6e",
#        )

        h_masked = pd.DataFrame(h_masked)
        h_masked.to_csv(
                mask_dir / f"map_flux_esa{tar_esa}.csv",
                index=False
            )
        

        for tt in [
            "cnts", "fser", "fsel", "fseu", "fvar", "fvto",
            "rate", "rvar", "stbg", "svar"
        ]:

#            map_data = np.loadtxt(
#                work_dir_hydrogen / f"map_{tt}_esa{tar_esa}.csv",
#                delimiter=",",
#                skiprows=1,
#            )
            filename = work_dir_hydrogen / f"map_{tt}_esa{tar_esa}.csv"
            df = pd.read_csv(filename)
            map_data = df.to_numpy()
            

            if map_data.shape != isn_mask.shape:
                raise ValueError(
                    f"pivot {pp}, ESA{tar_esa}, {tt}: map shape {map_data.shape} "
                    f"does not match mask shape {isn_mask.shape}"
                )

            map_masked = np.where(total_mask, np.nan, map_data)

#            np.savetxt(
#                mask_dir / f"map_{tt}_esa{tar_esa}.csv",
#                map_masked,
#                delimiter=",",
#                fmt="%.6e",
#            )

            map_masked = pd.DataFrame(map_masked)
            map_masked.to_csv(
                mask_dir / f"map_{tt}_esa{tar_esa}.csv",
                index=False
            )
        