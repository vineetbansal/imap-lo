"""
● Here's a summary of how the new script maps onto the old one:

  ┌────────────────────────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────┐
  │                                  07maps_from_goodtimes.py                                  │                               07maps_from_l1c.py                               │
  ├────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ calculate_spin_angles — load quaternion CDFs, rotate body-frame Z into ECLIPJ2000, average │ Dropped — L1C already has hae_longitude/hae_latitude per pixel                 │
  ├────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ create_ra_dec — NEP-anchored cone sweep across 60 bins per pivot angle                     │ Dropped — same reason                                                          │
  ├────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ filter_and_bin — MET conversion, good-time mask, accumulate per-bin                        │ Dropped — good-time masking happened upstream; replaced by LoPointingSet(ds)   │
  ├────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ inner loop in grid_and_calibrate — imap/jmap += counts[ia]                                 │ sky_map.project_pset_values_to_map(pset, ...)                                  │
  ├────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ reads scalar background from imap_lo_H_background_*.csv                                    │ reads h_background_rates from the L1C CDF itself, averaged over spatial pixels │
  ├────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ loops over 3 hardcoded PIVOT_ANGLES                                                        │ reads pivot_angle directly from the CDF                                        │
  └────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────┘

  Two things to be aware of before running it:

  1. SPICE kernels: match_coords_to_indices (called internally by project_pset_values_to_map) calls frame_transform to go from IMAP_HAE to IMAP_HAE. Even for a same-frame identity transform, SPICE needs the FK file that defines IMAP_HAE to be loaded. You'll need to furnish the imap frame kernels before calling maps_from_l1c.
  2. Background rate convention: h_background_rates in the L1C is per-pixel (shape (7, 3600, 40)), whereas grid_and_calibrate uses a single scalar from the separate background CSV. The script averages over spatial pixels as a reasonable substitute, but these won't be numerically identical.

"""
from pathlib import Path
import numpy as np
import pandas as pd
from imap_processing.cdf.utils import load_cdf
from imap_processing.ena_maps.ena_maps import LoPointingSet, RectangularSkyMap
from imap_processing.spice.geometry import SpiceFrame

ESA_ENERGY     = [0.016, 0.030, 0.056, 0.106, 0.200, 0.405, 0.787]
GEO_FACTOR     = [7.0e-5, 7.9e-5, 9.7e-5, 11.2e-5, 14.0e-5, 17.7e-5, 22.5e-5]
GEO_FACTOR_ERR = [4.9e-5, 5.5e-5, 6.8e-5, 3.0e-5, 4.5e-5, 2.0e-5, 1.4e-5]
N_ESA_LEVELS   = 7


def maps_from_l1c(l1c_cdf: Path, output_dir: Path) -> None:
    ds = load_cdf(l1c_cdf)

    # Replaces calculate_spin_angles + create_ra_dec + filter_and_bin from
    # 07maps_from_goodtimes.py. hae_longitude/hae_latitude are already computed
    # in the L1C CDF, so no quaternion loading or pivot-angle cone sweep is needed.
    # Good-time masking was applied upstream during L1C production.
    pset = LoPointingSet(ds)

    # Replaces the imap/jmap accumulation loop in grid_and_calibrate.
    # 6° spacing → 30 elevation × 60 azimuth pixels, matching the original grid.
    sky_map = RectangularSkyMap(spacing_deg=6.0, spice_frame=SpiceFrame.IMAP_HAE)
    sky_map.project_pset_values_to_map(pset, value_keys=["h_counts", "exposure_time"])

    # to_dataset() reshapes (pixel,) → (elevation, azimuth); squeeze the single epoch.
    map_ds = sky_map.to_dataset()
    counts = map_ds["h_counts"].values.squeeze(0)       # (7, 30, 60)
    expo   = map_ds["exposure_time"].values.squeeze(0)  # (7, 30, 60)

    # Per-ESA mean background rate from the L1C, replacing the scalar from
    # imap_lo_H_background_*.csv produced by 02autogt_convert.py.
    h_bgrate = ds["h_background_rates"].values[0].mean(axis=(-2, -1))  # (7,)

    pivot_angle = float(ds["pivot_angle"].values[0])
    output_dir.mkdir(parents=True, exist_ok=True)

    for esa_idx in range(N_ESA_LEVELS):
        bg     = h_bgrate[esa_idx]
        geo    = GEO_FACTOR[esa_idx]
        dge    = GEO_FACTOR_ERR[esa_idx]
        energy = ESA_ENERGY[esa_idx]

        mask  = expo[esa_idx] > 0
        rate  = np.where(mask, counts[esa_idx] / expo[esa_idx], 0.0)
        flux  = np.where(mask, rate / (geo * energy), 0.0)
        fser  = np.where(mask, rate * dge / (geo ** 2 * energy), 0.0)
        rvar  = np.where(mask, rate / expo[esa_idx], 0.0)
        fvar  = np.where(counts[esa_idx] > 0, flux ** 2 / counts[esa_idx], 0.0)
        fvto  = fvar + fser ** 2
        brate = np.where(mask, bg, 0.0)
        bvar  = np.where(mask, bg / expo[esa_idx], 0.0)
        bflux = np.where(mask, bg / (geo * energy), 0.0)
        bfvar = np.where(mask, bvar / (geo * energy) ** 2, 0.0)
        stbg  = np.where(mask & (bg > 0), rate / bg, 0.0)
        svar  = np.where(
            mask & (brate > 0) & (rate > 0),
            rvar / brate ** 2 + bvar / rate ** 2,
            0.0,
        )

        for name, data in [
            ("stbg", stbg), ("svar", svar), ("expo", expo[esa_idx]),
            ("cnts", counts[esa_idx]), ("rate", rate), ("flux", flux),
            ("fser", fser), ("rvar", rvar), ("fvar", fvar), ("fvto", fvto),
            ("brate", brate), ("bvar", bvar), ("bflux", bflux), ("bfvar", bfvar),
        ]:
            pd.DataFrame(data).to_csv(
                output_dir / f"map_pivot-{pivot_angle}_esa-{esa_idx + 1}_{name}.csv",
                index=False,
            )


if __name__ == "__main__":
    maps_from_l1c(
        Path("/media/vineetb/T7/imap/lo/l1c/2026/04/imap_lo_l1c_pset_20260412-repoint00216_v001.cdf"),
        Path("output/l1c_maps"),
    )
