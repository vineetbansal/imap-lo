import numpy as np
import pandas as pd
from pathlib import Path

PIVOT_ANGLES: list[float] = [75, 90, 105]
N_HISTOGRAM_BINS: int = 60
N_COLAT_BINS: int = 30
N_ESA_LEVELS: int = 7

# The following are indexed by ESA level (0-indexed, ESA level = index + 1)
ESA_ENERGY: list[float] = [0.016, 0.030, 0.056, 0.106, 0.200, 0.405, 0.787, 1.821]
GEO_FACTOR: list[float] = [7.0e-5, 7.9e-5, 9.7e-5, 11.2e-5, 14.0e-5, 17.7e-5, 22.5e-5, 6.721e-5]
GEO_FACTOR_ERR: list[float] = [4.9e-5, 5.5e-5, 6.8e-5, 3.0e-5, 4.5e-5, 2.0e-5, 1.4e-5, 6.721e-5]


def process(map_csv: Path, h_background_csv: Path, output_dir: Path, pivot_angles: list[float] | None = None):

    map_df = pd.read_csv(map_csv)
    h_bgrate = pd.read_csv(h_background_csv)['bg_rate'][0]
    output_dir.mkdir(parents=True, exist_ok=True)

    if pivot_angles is None:
        pivot_angles = PIVOT_ANGLES

    for pivot_angle in pivot_angles:
        for esa in range(N_ESA_LEVELS):

            df = map_df[(map_df['pivot_angle'] == pivot_angle) & (map_df['esa_level'] == esa + 1)]

            shape = (N_COLAT_BINS, N_HISTOGRAM_BINS)
            (
                h_cnts_map, exposure, h_rate_map, h_rate_var,
                h_flux_map, h_fvar_map, h_fser_map, h_fvto_map,
                back_rate_map, back_rate_var, back_flux_map, back_flux_var,
                stonoise_map, stonoise_var_map
            ) = [np.zeros(shape) for _ in range(14)]

            ps_ra = df['ecl_lon'].values
            ps_dec = df['ecl_lat'].values
            counts = df['counts'].values
            expo = df['expo'].values

            for ia in range(N_HISTOGRAM_BINS):
                ra = ps_ra[ia]
                dec = ps_dec[ia]

                theta = 90.0 + dec

                imap = int(ra * N_HISTOGRAM_BINS / 360.0)
                if imap == 60:
                    imap = 0

                jmap = int(theta * N_COLAT_BINS / 180.0)
                if jmap == 30:
                    jmap = 0

                h_cnts_map[jmap, imap] += counts[ia]
                exposure[jmap, imap] += expo[ia]

            for imap in range(0, N_HISTOGRAM_BINS):
                for jmap in range(0, N_COLAT_BINS):

                    expo = exposure[jmap, imap]

                    energy = ESA_ENERGY[esa]
                    geo = GEO_FACTOR[esa]
                    dge = GEO_FACTOR_ERR[esa]

                    # Only look up background rate if this bin has exposure,
                    # so we don't depend on YD when there were no input files.
                    if expo > 0:

                        back_rate_map[jmap, imap] = h_bgrate
                        back_rate_var[jmap, imap] = h_bgrate / expo
                        h_rate_map[jmap, imap] = h_cnts_map[jmap, imap] / expo
                        h_flux_map[jmap, imap] = h_rate_map[jmap, imap] / (geo * energy)
                        h_fser_map[jmap, imap] = h_rate_map[jmap, imap] * dge / (
                                    geo * geo * energy)
                        back_flux_map[jmap, imap] = h_bgrate / (geo * energy)
                        back_flux_var[jmap, imap] = back_rate_var[jmap, imap] / (
                                    geo * energy) ** 2
                        # represent uncertainty in terms of variance (Poisson counts)
                        h_rate_var[jmap, imap] = h_rate_map[jmap, imap] / expo
                        if h_bgrate > 0.0:
                            stonoise_map[jmap, imap] = h_rate_map[jmap, imap] / h_bgrate
                            # Guard against division by zero in stonoise_var components
                            if (back_rate_map[jmap, imap] > 0.0) and (
                                    h_rate_map[jmap, imap] > 0.0):
                                stonoise_var_map[jmap, imap] = (
                                        h_rate_var[jmap, imap] / back_rate_map[
                                    jmap, imap] ** 2
                                        + back_rate_var[jmap, imap] / h_rate_map[
                                            jmap, imap] ** 2
                                )
                            else:
                                stonoise_var_map[jmap, imap] = 0.0
                        # represent uncertainty in terms of variance (Poisson counts)
                        if h_cnts_map[jmap, imap] > 0.0:
                            h_fvar_map[jmap, imap] = h_flux_map[jmap, imap] ** 2 / \
                                                     h_cnts_map[jmap, imap]
                            h_fvto_map[jmap, imap] = h_flux_map[jmap, imap] ** 2 / \
                                                     h_cnts_map[jmap, imap] + h_fser_map[
                                                         jmap, imap] ** 2
                        else:
                            h_fvar_map[jmap, imap] = 0.0
                            h_fvto_map[jmap, imap] = h_fser_map[jmap, imap] ** 2

            for name, data in [
                ("stbg", stonoise_map),
                ("svar", stonoise_var_map),
                ("expo", exposure),
                ("cnts", h_cnts_map),
                ("rate", h_rate_map),
                ("flux", h_flux_map),
                ("fser", h_fser_map),
                ("rvar", h_rate_var),
                ("fvar", h_fvar_map),
                ("fvto", h_fvto_map),
                ("brate", back_rate_map),
                ("bvar", back_rate_var),
                ("bflux", back_flux_map),
                ("bfvar", back_flux_var),
            ]:
                pd.DataFrame(data).to_csv(output_dir / f"map_pivot-{pivot_angle}_esa-{esa+1}_{name}.csv", index=False)


if __name__ == "__main__":
    process(
        Path("output/map.csv"),
        Path("output/imap_lo_H_background_2026103.csv"),
        Path("output/maps")
    )