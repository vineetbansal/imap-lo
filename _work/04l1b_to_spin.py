# from quicklook/3S2_l1b_quickmaps/l1b_to_spin.py

from spacepy.pycdf import CDF
import numpy as np
from datetime import datetime
from pathlib import Path
import pandas as pd

N_ESA_LEVELS: int = 7
# Histogram angular bins (0-indexed) corresponding to the RAM and anti-RAM look directions
N_HISTOGRAM_BINS: int = 60
RAM_HISTOGRAM_BINS: tuple[slice, ...] = (slice(0, 20), slice(50, 60))
ANTI_RAM_HISTOGRAM_BINS: tuple[slice, ...] = (slice(20, 50),)
NEP_ROLL: int = RAM_HISTOGRAM_BINS[-1].stop - RAM_HISTOGRAM_BINS[
    -1].start  # length of the trailing RAM chunk that wraps to the front

PIVOT_ANGLES = [75, 90, 105]


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


def process(hist_cdf: Path, goodtime_file: Path, quaternion_files: list[Path],
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


if __name__ == "__main__":
    # input_hist_cdf, input_gt_file, input_hk_cdf, output_dir = sys.argv[1:]
    input_hist_cdf, goodtime_file, quaternion_files, output_dir = (
        "/media/vineetb/T7/imap/lo/l1b/2026/04/imap_lo_l1b_histrates_20260413-repoint00217_v002.cdf",
        "output/imap_lo_goodtimes_2026103.csv",
        ["/media/vineetb/T7/imap/spacecraft/l1a/2026/04/imap_spacecraft_l1a_quaternions_20260413_v001.cdf"],
        "output"
    )
    process(Path(input_hist_cdf), Path(goodtime_file),
            [Path(p) for p in quaternion_files], Path(output_dir))
