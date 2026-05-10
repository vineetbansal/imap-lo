import numpy as np
from pathlib import Path
import pandas as pd
import spiceypy
from spacepy import pycdf
from spacepy.time import Ticktock
from datetime import datetime
from textwrap import dedent
import imap_data_access

from imap_processing.cdf.imap_cdf_manager import ImapCdfAttributes
from imap_processing.lo.constants import LoConstants as c
from imap_processing.lo.l1b.lo_l1b import l1b_bgrates_and_goodtimes

import xarray as xr
from scipy.spatial.transform import Rotation
from imap_processing.spacecraft.quaternions import assemble_quaternions
from imap_processing.spice.geometry import get_spacecraft_to_instrument_spin_phase_offset, cartesian_to_spherical, \
    SpiceFrame
from imap_processing.spice.time import ttj2000ns_to_met
from imap_processing.cdf.utils import load_cdf


_SPICE_DIR = Path(__file__).parent.parent / "input_SPICE"

# ------------------
# Constants that should be migrated to imap_processing.lo.constants.LoConstants
N_SPIN_BINS: int = 60
N_COLAT_BINS: int = 30

NEP_ROLL: int = round(
    get_spacecraft_to_instrument_spin_phase_offset(
        SpiceFrame.IMAP_LO) * N_SPIN_BINS
)

# The following are indexed by ESA level (0-indexed, ESA level = index + 1)
ESA_ENERGY: list[float] = [0.016, 0.030, 0.056, 0.106, 0.200, 0.405, 0.787, 1.821]
GEO_FACTOR: list[float] = [7.0e-5, 7.9e-5, 9.7e-5, 11.2e-5, 14.0e-5, 17.7e-5, 22.5e-5, 6.721e-5]
GEO_FACTOR_ERR: list[float] = [4.9e-5, 5.5e-5, 6.8e-5, 3.0e-5, 4.5e-5, 2.0e-5, 1.4e-5, 6.721e-5]
# ------------------


def genererate_goodtimes(input_hist_cdf: Path, input_de_cdf: Path, input_hk_cdf: Path, output_dir: Path) -> tuple[float, Path, dict[str, float]]:
    """Run the good-times detection algorithm and write output files.

    Loads the L1B histogram, direct-events, and housekeeping CDFs, queries the
    ancillary background-rate overrides, and delegates to
    ``l1b_bgrates_and_goodtimes``.  Writes a good-times CSV to *output_dir* and
    returns the pivot angle, the CSV path, and per-element background rates.

    Parameters
    ----------
    input_hist_cdf : Path
        L1B histogram CDF file.
    input_de_cdf : Path
        L1B direct-events CDF file.
    input_hk_cdf : Path
        Housekeeping CDF file (used for ESA-step coarse-potential classification).
    output_dir : Path
        Destination directory; created if absent.

    Returns
    -------
    pivot_angle : float
        Pivot angle in degrees derived from the housekeeping dataset.
    goodtimes_csv : Path
        Path to the written ``imap_lo_goodtimes_<YYYYDDD>.csv`` file.
    bgrates : dict[str, float]
        Background rate (counts/s) keyed by element name (e.g. ``"H"``, ``"O"``).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if spiceypy.ktotal("all") == 0:
        spiceypy.furnsh(str(_SPICE_DIR / "lsk" / "naif0012.tls"))
        spiceypy.furnsh(str(_SPICE_DIR / "sclk" / "imap_sclk_0153.tsc"))

    with pycdf.CDF(str(input_hist_cdf)) as cdf:
        hist_epoch = pycdf.lib.v_datetime_to_tt2000(cdf['epoch'][:])
        hist_ds = xr.Dataset(
            coords={'epoch': xr.DataArray(hist_epoch, dims=['epoch'])}
        )
        for elem in c.ELEMS:
            field = f'{elem.lower()}_counts'
            hist_ds[field] = xr.DataArray(cdf[field][...], dims=['epoch', 'esa_step', 'spin_bin_6'])

    with pycdf.CDF(str(input_de_cdf)) as cdf:
        de_ds = xr.Dataset()
        if 'pivot_angle' in cdf:
            de_ds['pivot_angle'] = xr.DataArray([cdf['pivot_angle'][0]])

    with pycdf.CDF(str(input_hk_cdf)) as cdf:
        epoch_hk = pycdf.lib.v_datetime_to_tt2000(np.array(Ticktock(cdf['epoch'], 'CDF').UTC))
        hk_ds = xr.Dataset(
            coords={'epoch': xr.DataArray(epoch_hk, dims=['epoch'])}
        )
        if 'pcc_coarse_pot_pri' in cdf:
            hk_ds['pcc_coarse_pot_pri'] = xr.DataArray(cdf['pcc_coarse_pot_pri'][...], dims=['epoch'])

    epoch_dt = pycdf.lib.tt2000_to_datetime(int(hist_epoch[0]))
    date_str = f"{epoch_dt.year}{epoch_dt.timetuple().tm_yday:03d}"
    sci_dependencies = {
        'imap_lo_l1b_histrates': hist_ds,
        'imap_lo_l1b_de': de_ds,
        'imap_lo_l1b_nhk': hk_ds,
    }

    attr_mgr = ImapCdfAttributes()
    attr_mgr.add_instrument_global_attrs(instrument="lo")
    attr_mgr.add_instrument_variable_attrs(instrument="lo", level="l1b")

    anc_results = imap_data_access.query(
        table="ancillary",
        instrument="lo",
        descriptor="bg-rates-anti-ram-overrides",
    )
    anc_files = [imap_data_access.download(r["file_path"]) for r in anc_results]

    bgrates_ds, goodtimes_ds = l1b_bgrates_and_goodtimes(sci_dependencies, anc_files, attr_mgr)

    pivot_angle = goodtimes_ds["pivot"].item()

    goodtimes_csv = output_dir / f'imap_lo_goodtimes_{date_str}.csv'
    pd.DataFrame({
        'date': date_str,
        'begin': goodtimes_ds['gt_start_met'].values.astype(int),
        'end': goodtimes_ds['gt_end_met'].values.astype(int),
        'pivot': float(goodtimes_ds['pivot'].values),
        'pivot_de': float(goodtimes_ds['pivot_de'].values),
    }).to_csv(goodtimes_csv, header=True, index=False)

    bgrates = {
        elem: float(bgrates_ds[f'{elem.lower()}_background_rates'].values[0])
        for elem in c.ELEMS
    }

    return pivot_angle, goodtimes_csv, bgrates


def radec2cart(ra, colatitude_deg):
    """Convert right ascension and colatitude (degrees) to a Cartesian unit vector."""
    x = np.cos(np.radians(ra)) * np.sin(np.radians(colatitude_deg))
    y = np.sin(np.radians(ra)) * np.sin(np.radians(colatitude_deg))
    z = np.cos(np.radians(colatitude_deg))

    return np.array([x, y, z])



def create_ra_dec(spin_ecl_lon, spin_ecl_lat, pivot_angle) -> tuple[list[float], list[float], list[float]]:
    """
    Compute the ecliptic sky pointing for each of 60 spin-angle bins (6° each).

    All geometry is performed in ECLIPJ2000.  For a spacecraft spin axis defined
    by (spin_ecl_lon, spin_ecl_lat) and a pivot half-angle offset from that axis,
    sweeps 360° in 60 equal steps and converts each pointing direction to ecliptic
    longitude/latitude via ``cartesian_to_spherical``.  The perpendicular plane is
    oriented using the North Ecliptic Pole (= [0, 0, 1] in ECLIPJ2000) as a
    reference, giving a frame with axes toward the NEP and toward the ram direction.

    Parameters
    ----------
    spin_ecl_lon : float
        Spin axis ecliptic longitude in degrees (ECLIPJ2000).
    spin_ecl_lat : float
        Spin axis ecliptic latitude in degrees (ECLIPJ2000).
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
    spin_colatitude_deg = 90.0 - spin_ecl_lat

    pivot_angle_rad = np.radians(pivot_angle)

    def norm(v):
        return v / np.linalg.norm(v)

    # In ECLIPJ2000 the North Ecliptic Pole is exactly [0, 0, 1].
    nep_unit = np.array([0.0, 0.0, 1.0])
    spin_axis_unit = norm(radec2cart(spin_ecl_lon, spin_colatitude_deg))

    # Build a right-handed frame in the plane perpendicular to the spin axis,
    # anchored to the NEP so that spin-angle 0° points toward the pole.
    spin_perp_toward_nep = nep_unit - np.dot(nep_unit, spin_axis_unit) * spin_axis_unit
    spin_perp_toward_nep = norm(spin_perp_toward_nep)

    spin_perp_toward_ram = np.cross(spin_axis_unit, spin_perp_toward_nep)
    spin_perp_toward_ram = norm(spin_perp_toward_ram)

    # Step through 60 spin-angle bin centers (3°, 9°, …, 357°) and compute
    # the 3D pointing direction for each bin using the pivot-angle cone equation,
    # then read off ecliptic lon/lat via cartesian_to_spherical (ECLIPJ2000).
    bin_centers = np.arange(3, 360, 6).tolist()

    ecl_lons, ecl_lats = [], []
    for spin_angle_deg in bin_centers:
        pointing = (np.cos(pivot_angle_rad) * spin_axis_unit
                    + np.sin(pivot_angle_rad) * np.cos(np.radians(spin_angle_deg)) * spin_perp_toward_nep
                    + np.sin(pivot_angle_rad) * np.sin(np.radians(spin_angle_deg)) * spin_perp_toward_ram)
        _, ecl_lon, ecl_lat = cartesian_to_spherical(pointing[None])[0]
        ecl_lons.append(ecl_lon % 360)
        ecl_lats.append(ecl_lat)

    return bin_centers, ecl_lons, ecl_lats


def calculate_spin_angles(quaternion_files: list[Path], gt_begin: np.ndarray | None = None, gt_end: np.ndarray | None = None) -> tuple[float, float]:
    """Derive the mean spin-axis direction in equatorial J2000 from quaternion CDFs.

    Loads and concatenates one or more spacecraft quaternion CDF files, applies
    each attitude quaternion to the body-frame spin-axis vector ``[0, 0, 1]`` to
    obtain spin-axis directions in ECLIPJ2000, averages and normalises them, then
    applies a fixed frame rotation to J2000.

    Parameters
    ----------
    quaternion_files : list[Path]
        One or more L1A spacecraft quaternion CDF files covering the observation
        window.  Duplicates are deduplicated and files are sorted by epoch before
        concatenation.
    gt_begin : np.ndarray, optional
        Array of good-time interval start times in MET seconds.  When provided
        together with *gt_end*, attitude rows outside all intervals are dropped
        before computing the mean spin axis.
    gt_end : np.ndarray, optional
        Array of good-time interval end times in MET seconds (paired with
        *gt_begin*).

    Returns
    -------
    spin_ecl_lon : float
        Mean spin-axis ecliptic longitude in degrees (ECLIPJ2000).
    spin_ecl_lat : float
        Mean spin-axis ecliptic latitude in degrees (ECLIPJ2000).
    """
    quaternion_datasets = [load_cdf(dep) for dep in list(set(quaternion_files))]
    quaternion_datasets.sort(key=lambda ds: ds["epoch"].values[0])

    quaternion_ds = xr.concat(quaternion_datasets, dim="epoch")
    attitude_ds = assemble_quaternions(quaternion_ds)

    if gt_begin is not None and gt_end is not None:
        # attitude_ds epoch is already in MET seconds.
        attitude_met = attitude_ds["epoch"].values
        attitude_mask = np.any(
            (attitude_met[:, None] >= gt_begin) & (attitude_met[:, None] <= gt_end),
            axis=1,
        )
        attitude_ds = attitude_ds.isel(epoch=attitude_mask)

    # Apply each attitude quaternion to the spin-axis body vector to get the spin
    # axis in ECLIPJ2000. This uses the quaternion data directly to avoid requiring
    # SPICE CK (attitude) kernels, which are not loaded in this pipeline path.
    quaternion_array = np.column_stack(
        [attitude_ds["quat_x"], attitude_ds["quat_y"], attitude_ds["quat_z"],
         attitude_ds["quat_s"]])
    mean_spin_axis_eclipj2000 = Rotation.from_quat(quaternion_array).apply(
        [0., 0., 1.]).mean(axis=0)
    mean_spin_axis_eclipj2000 /= np.linalg.norm(mean_spin_axis_eclipj2000)

    spin_ecl_lon, spin_ecl_lat = cartesian_to_spherical(mean_spin_axis_eclipj2000[None])[0, 1:]
    return spin_ecl_lon % 360, spin_ecl_lat


def filter_and_bin(pivot_angle: float, hist_cdf: Path, goodtime_file: Path, quaternion_files: list[Path],
            output_dir: Path) -> Path:
    """Mask histogram records to good-time intervals and accumulate counts per spin-angle bin.

    For each ESA level the function:

    1. Converts CDF epoch timestamps to MET seconds and keeps only records that
       fall within at least one good-time interval from *goodtime_file*.
    2. Computes the ecliptic sky pointing of the 60 spin-angle bins (6° each) from
       the mean spin axis and the pivot angle.
    3. Sums ``h_counts`` and ``exposure_time_6deg`` over the good-time-masked
       records, rolls the result by ``NEP_ROLL`` so that RAM bins are contiguous,
       and appends a row per bin to the output CSV.

    Parameters
    ----------
    pivot_angle : float
        Pivot (half-cone) angle in degrees used to compute sky pointing.
    hist_cdf : Path
        L1B histogram CDF file containing ``h_counts`` and ``exposure_time_6deg``.
    goodtime_file : Path
        Good-times CSV produced by :func:`genererate_goodtimes` with ``begin``/
        ``end`` MET columns.
    quaternion_files : list[Path]
        Spacecraft quaternion CDF files passed to :func:`calculate_spin_angles`.
    output_dir : Path
        Destination directory for ``map.csv``; created if absent.

    Returns
    -------
    map_csv : Path
        Path to the written ``map.csv`` flat table with columns
        ``esa_level``, ``bins``, ``ecl_lon``, ``ecl_lat``, ``counts``,
        ``expo``, ``spin_ra``, ``spin_dec``.
    """

    if spiceypy.ktotal("all") == 0:
        spiceypy.furnsh(str(_SPICE_DIR / "lsk" / "naif0012.tls"))
        spiceypy.furnsh(str(_SPICE_DIR / "sclk" / "imap_sclk_0153.tsc"))

    cdf = pycdf.CDF(str(hist_cdf))

    # Convert CDF epoch (datetime objects) to MET seconds via SPICE, then mask
    # to records that fall within at least one goodtime interval.
    tt2000_ns = pycdf.lib.v_datetime_to_tt2000(cdf['epoch'][:])
    met_sec = ttj2000ns_to_met(tt2000_ns)
    gt_df = pd.read_csv(goodtime_file)

    mask = np.any(
        (met_sec[:, None] >= gt_df['begin'].values) & (
                    met_sec[:, None] <= gt_df['end'].values),
        axis=1,
    )

    spin_ecl_lon, spin_ecl_lat = calculate_spin_angles(quaternion_files, gt_df['begin'].values, gt_df['end'].values)

    bins, ecl_lons, ecl_lats = create_ra_dec(spin_ecl_lon, spin_ecl_lat, pivot_angle)
    pivot_df = pd.DataFrame({
        'bins': bins,
        'bin_ecl_lon': ecl_lons,
        'bin_ecl_lat': ecl_lats,
    })

    dataframes = []
    for esa_level in range(c.N_ESA_LEVELS):
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
        df['spin_ecl_lon'] = spin_ecl_lon
        df['spin_ecl_lat'] = spin_ecl_lat
        dataframes.append(df)

    output_dir.mkdir(parents=True, exist_ok=True)
    map_csv = output_dir / "map.csv"
    pd.concat(dataframes, ignore_index=True).to_csv(map_csv,
                                                    index=False)

    return map_csv


def grid_and_calibrate(map_csv: Path, h_bgrate: float, output_dir: Path) -> Path:
    """Project spin-angle bins onto a 30×60 ecliptic sky grid and apply flux calibration.

    Reads ``map.csv`` from :func:`filter_and_bin` and, for each ESA level, maps
    the 60 spin-angle bins onto a colatitude × longitude grid
    (30 × 6° colatitude bins, 60 × 6° longitude bins).  Counts and exposure
    accumulate additively for bins that share the same sky pixel.  For every
    pixel with non-zero exposure the following quantities are computed and written
    to individual CSVs: ``cnts``, ``expo``, ``rate``, ``rvar``, ``flux``,
    ``fvar``, ``fser``, ``fvto``, ``brate``, ``bvar``, ``bflux``, ``bfvar``,
    ``stbg``, ``svar``.

    Parameters
    ----------
    map_csv : Path
        Flat CSV produced by :func:`filter_and_bin`.
    h_bgrate : float
        Hydrogen background rate (counts/s) used to compute background-subtracted
        quantities (``brate``, ``stbg``, etc.).
    output_dir : Path
        Destination directory for per-quantity CSVs; created if absent.

    Returns
    -------
    output_dir : Path
        The directory containing the written ``map_esa-{level}_{quantity}.csv``
        files (one per ESA level × quantity combination).
    """

    map_df = pd.read_csv(map_csv)
    output_dir.mkdir(parents=True, exist_ok=True)

    for esa in range(c.N_ESA_LEVELS):

        df = map_df[map_df['esa_level'] == esa + 1]

        shape = (N_COLAT_BINS, N_SPIN_BINS)
        (
            h_cnts_map, exposure, h_rate_map, h_rate_var,
            h_flux_map, h_fvar_map, h_fser_map, h_fvto_map,
            back_rate_map, back_rate_var, back_flux_map, back_flux_var,
            stonoise_map, stonoise_var_map
        ) = [np.zeros(shape) for _ in range(14)]

        ps_ra = df['bin_ecl_lon'].values
        ps_dec = df['bin_ecl_lat'].values
        counts = df['counts'].values
        expo = df['expo'].values

        for ia in range(N_SPIN_BINS):
            ra = ps_ra[ia]
            dec = ps_dec[ia]

            theta = 90.0 + dec

            imap = int(ra * N_SPIN_BINS / 360.0)
            if imap == 60:
                imap = 0

            jmap = int(theta * N_COLAT_BINS / 180.0)
            if jmap == 30:
                jmap = 0

            h_cnts_map[jmap, imap] += counts[ia]
            exposure[jmap, imap] += expo[ia]

        for imap in range(0, N_SPIN_BINS):
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
            pd.DataFrame(data).to_csv(output_dir / f"map_esa-{esa+1}_{name}.csv", header=False, index=False)

    return output_dir


def write_soc(map_dir: Path, output_dir: Path):
    """Convert per-quantity calibration CSVs to SOC-compatible text files.

    For every ``map_*.csv`` in *map_dir* (30-row × 60-column matrices produced by
    :func:`grid_and_calibrate`) writes a ``.txt`` file with the same stem to
    *output_dir*.  Each file begins with a structured comment header that encodes
    axis ranges, title, units, frame metadata (ECLIPJ2000 sky frame, J2000
    position frame), and instrument geometry constants, followed by
    tab-separated rows of scientific-notation values.

    Parameters
    ----------
    map_dir : Path
        Directory containing ``map_*.csv`` files from :func:`grid_and_calibrate`.
    output_dir : Path
        Destination directory for the ``.txt`` files; created if absent.

    Returns
    -------
    output_dir : Path
        The directory containing the written SOC ``.txt`` files.
    """

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

        return dedent(f"""
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
            # """).splitlines()

    output_dir.mkdir(parents=True, exist_ok=True)

    for csv_file in Path(map_dir).glob(f"map_*.csv"):

        df = pd.read_csv(csv_file, header=None, index_col=False)

        data = df.to_numpy(dtype=float)
        assert data.shape == (30, 60)

        h_min = np.nanmin(data)
        h_max = np.nanmax(data)

        header = build_header(csv_file.stem, h_min, h_max)

        with open(output_dir / (csv_file.stem + ".txt"), "w") as f:
            f.write("\n".join(header) + "\n")
            for row in data:
                f.write("\t".join(f"{val:.6e}" for val in row) + "\n")

    return output_dir


if __name__ == "__main__":

    # Input files - day-specific
    # These are the files we will get from sds-data-manager once all the code is in
    # imap_processing and sds-data-manager has been updated with the correct
    # dependencies.
    input_hist_cdf, input_de_cdf, input_hk_cdf, quaternion_files = (
        Path("inputs/imap_lo_l1b_histrates_20260413-repoint00217_v002.cdf"),
        Path("inputs/imap_lo_l1b_de_20260413-repoint00217_v002.cdf"),
        Path("inputs/imap_lo_l1b_nhk_20260413-repoint00217_v001.cdf"),

        # quaternion_files is a list since multiple files may cover our single
        # date under consideration.
        [
            Path("inputs/imap_spacecraft_l1a_quaternions_20260413_v001.cdf"),
            Path("inputs/imap_spacecraft_l1a_quaternions_20260414_v001.cdf")
         ]
    )

    output_dir = Path("output")

    pivot_angle, goodtimes_csv, bgrates = genererate_goodtimes(input_hist_cdf, input_de_cdf, input_hk_cdf, output_dir)
    h_bgrate = bgrates["H"]

    map_csv = filter_and_bin(pivot_angle, input_hist_cdf, goodtimes_csv, quaternion_files, output_dir)

    maps_path = grid_and_calibrate(map_csv, h_bgrate, output_dir / "maps")

    soc_path = write_soc(maps_path, output_dir / "soc")