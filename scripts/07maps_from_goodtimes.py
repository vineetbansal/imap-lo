from spacepy.pycdf import CDF
import numpy as np
from datetime import datetime
from pathlib import Path
import pandas as pd

N_ESA_LEVELS: int = 7
# Histogram angular bins (0-indexed) corresponding to the RAM and anti-RAM look directions
N_HISTOGRAM_BINS: int = 60
N_COLAT_BINS: int = 30

RAM_HISTOGRAM_BINS: tuple[slice, ...] = (slice(0, 20), slice(50, 60))
ANTI_RAM_HISTOGRAM_BINS: tuple[slice, ...] = (slice(20, 50),)
NEP_ROLL: int = RAM_HISTOGRAM_BINS[-1].stop - RAM_HISTOGRAM_BINS[
    -1].start  # length of the trailing RAM chunk that wraps to the front

PIVOT_ANGLES = [75, 90, 105]

# The following are indexed by ESA level (0-indexed, ESA level = index + 1)
ESA_ENERGY: list[float] = [0.016, 0.030, 0.056, 0.106, 0.200, 0.405, 0.787, 1.821]
GEO_FACTOR: list[float] = [7.0e-5, 7.9e-5, 9.7e-5, 11.2e-5, 14.0e-5, 17.7e-5, 22.5e-5, 6.721e-5]
GEO_FACTOR_ERR: list[float] = [4.9e-5, 5.5e-5, 6.8e-5, 3.0e-5, 4.5e-5, 2.0e-5, 1.4e-5, 6.721e-5]


def radec2cart(ra, colatitude_deg):
    x = np.cos(np.radians(ra)) * np.sin(np.radians(colatitude_deg))
    y = np.sin(np.radians(ra)) * np.sin(np.radians(colatitude_deg))
    z = np.cos(np.radians(colatitude_deg))

    return np.array([x, y, z])


def equatorial_to_ecliptic(alpha, delta):
    # Obliquity of ecliptic at J2000.0 epoch
    epsilon_0 = 23.43929111  # degrees

    alpha_rad = np.radians(alpha)
    delta_rad = np.radians(delta)
    epsilon_rad = np.radians(epsilon_0)

    numerator = np.sin(alpha_rad) * np.cos(epsilon_rad) + np.tan(delta_rad) * np.sin(
        epsilon_rad)
    denominator = np.cos(alpha_rad)

    # Calculate ecliptic longitude
    lambda_ecl_rad = np.arctan2(numerator, denominator)

    # Calculate ecliptic latitude
    beta_ecl_rad = np.arcsin(np.sin(delta_rad) * np.cos(epsilon_rad) -
                             np.cos(delta_rad) * np.sin(epsilon_rad) * np.sin(
        alpha_rad))

    lambda_ecl = np.degrees(lambda_ecl_rad)
    beta_ecl = np.degrees(beta_ecl_rad)

    lambda_ecl = lambda_ecl % 360

    return lambda_ecl, beta_ecl


def create_ra_dec(spin_axis_ra, spin_axis_dec, pivot_angle) -> tuple[list[float], list[float], list[float]]:
    """
    Compute the ecliptic sky pointing for each of 60 spin-angle bins (6° each).

    For a spacecraft spin axis defined by (spin_axis_ra, spin_axis_dec) and a pivot half-angle
    offset from that axis, sweeps 360° in 60 equal steps and converts each
    pointing direction from equatorial Cartesian to ecliptic longitude/latitude.
    The perpendicular plane is oriented using the North Ecliptic Pole as a
    reference, giving a frame with axes toward the NEP and toward the ram direction.

    Parameters
    ----------
    spin_axis_ra : float
        Spin axis right ascension in degrees (equatorial J2000).
    spin_axis_dec : float
        Spin axis declination in degrees (equatorial J2000).
    pivot_angle : float
        Half-angle offset from the spin axis in degrees.

    Returns
    -------
    bin_centers : list of float
        Spin angle bin centers (degrees) for each of the 60 bin centers.
    ecl_lons : list of float
        Ecliptic longitude (degrees, 0–360) for each of the 60 bin centers.
    ecl_lats : list of float
        Ecliptic latitude (degrees) for each of the 60 bin centers.
    """
    spin_colatitude_deg = 90.0 - spin_axis_dec

    nep_ra, nep_dec = 270, 66.56  # Standard NEP direction in J2000
    nep_colatitude_deg = 90.0 - nep_dec

    pivot_angle_rad = np.radians(pivot_angle)

    def norm(v):
        return v / np.linalg.norm(v)

    nep_unit = norm(radec2cart(nep_ra, nep_colatitude_deg))
    spin_axis_unit = norm(radec2cart(spin_axis_ra, spin_colatitude_deg))

    # Build a right-handed frame in the plane perpendicular to the spin axis,
    # anchored to the NEP so that spin-angle 0° points toward the pole.
    spin_perp_toward_nep = nep_unit - np.dot(nep_unit,
                                             spin_axis_unit) * spin_axis_unit  # NEP projected onto spin-perp plane
    spin_perp_toward_nep = norm(spin_perp_toward_nep)

    spin_perp_toward_ram = np.cross(spin_axis_unit,
                                    spin_perp_toward_nep)  # completes the right-handed frame (ram direction)
    spin_perp_toward_ram = norm(spin_perp_toward_ram)

    # Step through 60 spin-angle bin centers (3°, 9°, …, 357°) and compute
    # the 3D pointing direction for each bin using the pivot-angle cone equation,
    # then convert equatorial Cartesian → ecliptic lon/lat.
    bin_centers = np.arange(3, 360, 6).tolist()

    ecl_lons, ecl_lats = [], []
    for spin_angle_deg in bin_centers:
        x, y, z = np.cos(pivot_angle_rad) * spin_axis_unit + np.sin(
            pivot_angle_rad) * np.cos(
            np.radians(spin_angle_deg)) * spin_perp_toward_nep + np.sin(
            pivot_angle_rad) * np.sin(
            np.radians(spin_angle_deg)) * spin_perp_toward_ram

        ecl_lon, ecl_lat = equatorial_to_ecliptic(np.degrees(np.arctan2(y, x)),
                                                  np.degrees(np.arcsin(z)))
        ecl_lons.append(ecl_lon)
        ecl_lats.append(ecl_lat)

    return bin_centers, ecl_lons, ecl_lats


def calculate_spin_angles(quaternion_files: list[Path]) -> tuple[float, float]:
    import xarray as xr
    from scipy.spatial.transform import Rotation
    from imap_processing.spacecraft.quaternions import assemble_quaternions
    from imap_processing.spice.geometry import cartesian_to_spherical, frame_transform, \
        SpiceFrame
    from imap_processing.cdf.utils import load_cdf

    quaternion_datasets = [load_cdf(dep) for dep in list(set(quaternion_files))]
    quaternion_datasets.sort(key=lambda ds: ds["epoch"].values[0])

    quaternion_ds = xr.concat(quaternion_datasets, dim="epoch")
    attitude_ds = assemble_quaternions(quaternion_ds)

    # Apply each attitude quaternion to the spin-axis body vector to get the spin
    # axis in ECLIPJ2000. This uses the quaternion data directly to avoid requiring
    # SPICE CK (attitude) kernels, which are not loaded in this pipeline path.
    quaternion_array = np.column_stack(
        [attitude_ds["quat_x"], attitude_ds["quat_y"], attitude_ds["quat_z"],
         attitude_ds["quat_s"]])
    mean_spin_axis_eclipj2000 = Rotation.from_quat(quaternion_array).apply(
        [0., 0., 1.]).mean(axis=0)
    mean_spin_axis_eclipj2000 /= np.linalg.norm(mean_spin_axis_eclipj2000)

    # ECLIPJ2000 -> J2000 is a fixed rotation between two built-in SPICE inertial
    # frames; no kernel files are required and et is irrelevant.
    mean_spin_axis_j2000 = frame_transform(0.0, mean_spin_axis_eclipj2000,
                                           SpiceFrame.ECLIPJ2000, SpiceFrame.J2000)

    spin_ra, spin_dec = cartesian_to_spherical(mean_spin_axis_j2000[None])[0, 1:]
    return spin_ra, spin_dec


def process1(hist_cdf: Path, goodtime_file: Path, quaternion_files: list[Path],
            output_dir: Path, pivot_angles: list[float] | None = None):
    if pivot_angles is None:
        pivot_angles = PIVOT_ANGLES

    spin_ra, spin_dec = calculate_spin_angles(quaternion_files)
    spin_ecl_lon, spin_ecl_lat = equatorial_to_ecliptic(spin_ra, spin_dec)

    cdf = CDF(str(hist_cdf))

    # Convert CDF epoch (datetime objects) to MET seconds, then mask to
    # records that fall within at least one goodtime interval.
    # TODO: Why not the 9s offset that was used in the gt csv file creation?
    met_reference_epoch = datetime(2010, 1, 1, 0, 0, 0)
    met_sec = np.array(
        [(e - met_reference_epoch).total_seconds() for e in cdf['epoch'][:]])
    gt_df = pd.read_csv(goodtime_file)

    mask = np.any(
        (met_sec[:, None] >= gt_df['begin'].values) & (
                    met_sec[:, None] <= gt_df['end'].values),
        axis=1,
    )

    pivot_dfs = []
    for pivot_angle in pivot_angles:
        bins, ecl_lons, ecl_lats = create_ra_dec(spin_ecl_lon, spin_ecl_lat, pivot_angle)
        pivot_dfs.append(pd.DataFrame({
            'pivot_angle': pivot_angle,
            'bins': bins,
            'ecl_lon': ecl_lons,
            'ecl_lat': ecl_lats,
        }))
    pivot_df = pd.concat(pivot_dfs, ignore_index=True)

    dataframes = []
    for esa_level in range(N_ESA_LEVELS):
        hist_counts = np.sum(cdf['h_counts'][...][mask, esa_level, :].T, axis=1)
        exposure = np.sum(cdf['exposure_time_6deg'][...][mask, esa_level, :].T, axis=1)

        # Rolling by NEP_ROLL brings the trailing RAM chunk (bins 50–59) to the front,
        # making the RAM bins contiguous.
        # NEP bins 0–29 (0–180 deg) = RAM, 30–59 (180–360 deg) = anti-RAM
        nep_counts = np.roll(hist_counts, NEP_ROLL)
        nep_exposure = np.roll(exposure, NEP_ROLL)

        esa_df = pd.DataFrame({'bins': bins, 'counts': nep_counts, 'expo': nep_exposure})
        df = pivot_df.merge(esa_df, on='bins')
        df.insert(0, 'esa_level', esa_level + 1)
        df['spin_ra'] = spin_ecl_lon
        df['spin_dec'] = spin_ecl_lat
        dataframes.append(df)

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(dataframes, ignore_index=True).to_csv(f"{output_dir}/map.csv",
                                                    index=False)


def process2(map_csv: Path, h_background_csv: Path, output_dir: Path, pivot_angles: list[float] | None = None):

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


def process3(map_dir: Path, output_dir: Path, pivot_angles: list[float] | None = None):

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
    input_hist_cdf, goodtime_file, quaternion_files, output_dir = (
        "/media/vineetb/T7/imap/lo/l1b/2026/04/imap_lo_l1b_histrates_20260413-repoint00217_v002.cdf",
        "output/imap_lo_goodtimes_2026103.csv",
        ["/media/vineetb/T7/imap/spacecraft/l1a/2026/04/imap_spacecraft_l1a_quaternions_20260413_v001.cdf"],
        "output"
    )
    process1(Path(input_hist_cdf), Path(goodtime_file),
            [Path(p) for p in quaternion_files], Path(output_dir))

    process2(
        Path("output/map.csv"),
        Path("output/imap_lo_H_background_2026103.csv"),
        Path("output/maps")
    )

    process3(
        Path("output/maps"),
        Path("output/soc")
    )