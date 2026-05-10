import numpy as np
from scipy.spatial.transform import Rotation

from imap_processing.spacecraft.quaternions import assemble_quaternions
from imap_processing.cdf.utils import load_cdf
from imap_processing.spice.geometry import cartesian_to_spherical

cdfs = ("/media/vineetb/T7/imap/spacecraft/l1a/2026/04/imap_spacecraft_l1a_quaternions_20260413_v001.cdf", "/media/vineetb/T7/imap/spacecraft/l1a/2026/04/imap_spacecraft_l1a_quaternions_20260414_v001.cdf")

for cdf in cdfs:
    ds = load_cdf(cdf)
    l1b = assemble_quaternions(ds)

    quats = np.column_stack([l1b["quat_x"], l1b["quat_y"], l1b["quat_z"], l1b["quat_s"]])
    mean_ecl = Rotation.from_quat(quats).apply([0., 0., 1.]).mean(axis=0)
    mean_ecl /= np.linalg.norm(mean_ecl)

    # Obliquity for ECLIPJ2000 -> J2000
    eps = np.radians(23.439291)
    R_obliq = np.array(
        [[1, 0, 0], [0, np.cos(eps), -np.sin(eps)], [0, np.sin(eps), np.cos(eps)]])
    mean_j2000 = R_obliq @ mean_ecl

    spinra, spindec = cartesian_to_spherical(mean_j2000[None])[0, 1:]

    print(spinra, spindec)