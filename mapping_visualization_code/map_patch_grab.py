import matplotlib.pyplot as plt
from astropy.wcs import WCS

def map_image(data, header, title=None, grid=True, cmap=None):
    """
    Display an astronomical image using its WCS (IDL map_image equivalent).

    Parameters
    ----------
    data : 2D ndarray
        Image array
    header : FITS header
        WCS header
    title : str
        Plot title
    grid : bool
        Show coordinate grid
    cmap : str or None
        Matplotlib colormap
    """

    wcs = WCS(header)

    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111, projection=wcs)

    im = ax.imshow(data, origin="lower", cmap=cmap)

    if grid:
        ax.grid(ls=":", alpha=0.6)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    if title:
        ax.set_title(title)

    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.show()




import numpy as np
from astropy.wcs import WCS
from reproject import reproject_interp

def map_patch(base_data, base_header, patch_data, patch_header,
              method="interp", fill_value=np.nan):
    """
    Insert patch_data into base_data using WCS alignment.

    Parameters
    ----------
    base_data : 2D ndarray
        Destination image
    base_header : FITS header
        WCS for destination
    patch_data : 2D ndarray
        Image to insert
    patch_header : FITS header
        WCS for patch
    method : str
        'interp' or 'nearest'
    fill_value : float
        Value treated as empty in patch

    Returns
    -------
    out : 2D ndarray
        Patched image
    footprint : 2D ndarray
        Where patch contributed (0–1)
    """

    if method == "interp":
        reproj, footprint = reproject_interp(
            (patch_data, patch_header),
            base_header,
            shape_out=base_data.shape
        )
    else:
        from reproject import reproject_exact
        reproj, footprint = reproject_exact(
            (patch_data, patch_header),
            base_header,
            shape_out=base_data.shape
        )

    out = base_data.copy()

    mask = np.isfinite(reproj) & (footprint > 0)
    out[mask] = reproj[mask]

    return out, footprint



import numpy as np
import matplotlib.pyplot as plt

from astropy.wcs import WCS
from astropy.io import fits
from astropy.wcs.utils import proj_plane_pixel_scales
from reproject import reproject_interp

# -------------------------------------------------
# 1. Create a base all-sky Mollweide WCS
# -------------------------------------------------
nx, ny = 360, 180

wcs_base = WCS(naxis=2)
wcs_base.wcs.ctype = ["RA---MOL", "DEC--MOL"]
wcs_base.wcs.crval = [0, 0]        # center RA, Dec
wcs_base.wcs.crpix = [nx/2, ny/2]
wcs_base.wcs.cdelt = [-1.0, 1.0]   # deg per pixel

base_data = np.zeros((ny, nx))

# -------------------------------------------------
# 2. Create a smaller patch (Gaussian blob)
# -------------------------------------------------
px, py = 60, 40
wcs_patch = WCS(naxis=2)
wcs_patch.wcs.ctype = ["RA---TAN", "DEC--TAN"]
wcs_patch.wcs.crval = [45, 10]     # patch center
wcs_patch.wcs.crpix = [px/2, py/2]
wcs_patch.wcs.cdelt = [-0.5, 0.5]

y, x = np.mgrid[:py, :px]
patch_data = np.exp(-((x-px/2)**2 + (y-py/2)**2)/200.)

# -------------------------------------------------
# 3. Reproject patch onto Mollweide grid
# -------------------------------------------------
reproj, footprint = reproject_interp(
    (patch_data, wcs_patch),
    wcs_base,
    shape_out=base_data.shape
)

patched = base_data.copy()
mask = footprint > 0
patched[mask] = reproj[mask]

# -------------------------------------------------
# 4. Plot in Mollweide projection
# -------------------------------------------------
fig = plt.figure(figsize=(10,5))
ax = fig.add_subplot(111, projection=wcs_base)

im = ax.imshow(patched, origin="lower")
ax.grid(color="gray", ls=":")

ax.set_xlabel("Right Ascension")
ax.set_ylabel("Declination")
ax.set_title("Patched map in Mollweide projection")

plt.colorbar(im, ax=ax, shrink=0.8)
plt.show()
