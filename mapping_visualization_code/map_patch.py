import matplotlib.pyplot as plt
from astropy.wcs import WCS
import numpy as np
import pandas as pd
from astropy.io import fits
import matplotlib.pyplot as plt
from reproject import reproject_interp, reproject_exact
import astropy.units as u
from matplotlib.colors import LogNorm
from scipy.ndimage import gaussian_filter
from scipy.interpolate import griddata
import cartopy.crs as ccrs
from scipy.spatial.transform import Rotation as R

def sph_to_cart(lat, lon):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    return np.array([x, y, z])

def rotation_matrix_to_center(new_colat0, new_lon0):
    # Step 1: rotate around Z axis by -lon0
    r1 = R.from_euler('z', -new_lon0, degrees=True)
    # Step 2: rotate around Y axis by 90-lat0
    r2 = R.from_euler('y', 90-new_colat0, degrees=True)
    # Combined rotation
    return r2 * r1

def inverse_rotation_matrix_to_center(rot, xyz_rot):
    """
    Apply inverse rotation to xyz_rot points.
    rot: scipy.spatial.transform.Rotation object used in forward rotation
    xyz_rot: shape (N,3)
    Returns xyz_orig (N,3)
    """
    return rot.inv().apply(xyz_rot)

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



data = pd.read_csv("map_flux_esa7.csv", header=0).values
print(data.shape)   # confirm dimensions

#2️⃣ Create a WCS for the patch

#You need to decide what the axes represent.
#Most heliospheric / sky maps use:

#X → longitude (0–360)

#Y → latitude (−90–90)

# Here’s a simple plate carrée WCS:

ny, nx = data.shape


# Original grid
# wrong. nlat, nlon = 180, 360
lats = np.linspace(-90, 90, ny)
print(lats)
lons = np.linspace(0, 360, nx)
print(lons)
# data = np.random.rand(nlat, nlon)  # your original data

# Flatten the grid
lon_grid, lat_grid = np.meshgrid(lons, lats)
print(lat_grid)
xyz = sph_to_cart(lat_grid, lon_grid)
xyz_flat = xyz.reshape(3, -1).T  # shape (N, 3)
print(xyz_flat[0,:])
print(xyz_flat[1,:])
print(xyz_flat[:,0])

# Rotate
new_colat0 = 90
new_lon0 = 40
theta = np.radians(new_colat0)
phi = np.radians(new_lon0)

rot = rotation_matrix_to_center(new_colat0=new_colat0, new_lon0=new_lon0)  # example

xyz = [np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi), np.cos(theta) ]
print(xyz)
xyz_r = rot.apply(xyz)
print(xyz_r)
l_r = np.degrees(np.arctan2(xyz_r[1], xyz_r[0]))
print("rotated long", l_r)
xyz_inv = rot.inv().apply(xyz_r)
l_i = np.degrees(np.arctan2(xyz_inv[1], xyz_inv[0]))
print("inverse long",l_i)

xyz_rot = rot.apply(xyz_flat)

# Convert back to lat/lon
lat_rot = np.degrees(np.arcsin(xyz_rot[:, 2]))
lon_rot = np.degrees(np.arctan2(xyz_rot[:, 1], xyz_rot[:, 0]))
# lon_rot = (lon_rot + 360) % 360  # keep in [0,360]
lon_rot = (lon_rot + 180) % 360 - 180

lat_rot = lat_rot.reshape(ny, nx)
lon_rot = lon_rot.reshape(ny, nx)
lon_rot = (lon_rot + 180) % 360 - 180

# Regular target grid
#new_lats = np.linspace(-87, 87, ny)
new_lats = np.linspace(-90, 90, ny)
new_lons = np.linspace(0.0, 360.0, nx)
new_lons = (new_lons + 180) % 360 - 180

# Regular target grid (PlateCarree expects -180..180)

#new_lons = np.linspace(-177, 183, nx)

lon_new_grid, lat_new_grid = np.meshgrid(new_lons, new_lats)
lon_new_grid = (lon_new_grid + 180) % 360 - 180

# note that actual long is negative of new_lons
#lon_new_grid, lat_new_grid = np.meshgrid(new_lons, new_lats)

#points = np.column_stack((lat_rot.ravel(), lon_rot.ravel()))
#print(points)
#values = data.ravel()
#print(values)

# Reverse longitude for “outside view”
# lon_flipped = (360 - lon_new_grid) % 360
# lon_rot_flipped = (360 - lon_rot) % 360
lon_flipped = lon_new_grid
lon_rot_flipped = lon_rot

#data_rot_flipped = griddata(
#    points=points,
#    values=values,
#    xi=(lat_new_grid, lon_flipped),
#    method='cubic',  fill_value=0.0 
#)

points = np.column_stack((lon_rot.ravel(), lat_rot.ravel()))
values = data.ravel()

vmin, vmax = 10, 160

data_rot = griddata(
    points,
    values,
    (lon_new_grid, lat_new_grid),
#    (lon_rot, lat_rot),
    method="cubic",      # cubic often overshoots
    fill_value=0.0
)

# Fill NaNs at edges (nearest)
#mask = np.isnan(data_rot_flipped)
#data_rot_flipped[mask] = griddata(
#    points=np.column_stack((lat_rot.ravel(), lon_rot_flipped.ravel())),
#    values=values.ravel(),
#    xi=(lat_new_grid[mask], lon_flipped[mask]),
#    method='nearest',  fill_value=0.0 
#)


data_clipped = np.clip(data_rot, vmin, vmax)
data_filled = np.copy(data_clipped)
data_filled[np.isnan(data_filled)] = vmin  # or some constant

#data_masked = np.ma.masked_less_equal(data_rot_flipped, vmin)  # mask zeros or negatives

fig, ax = plt.subplots(subplot_kw={'projection': ccrs.Mollweide()})

# --- display (center-aligned)
#im = ax.imshow(
#    data_clipped,
#    extent=[-180, 180, new_lats.min(), new_lats.max()],
#    transform=ccrs.PlateCarree(),
#    origin="lower",
#    cmap="viridis",
#    norm=LogNorm(vmin=vmin, vmax=vmax)
#)

im = ax.imshow(
    data_filled,
    extent=[lon_rot.min(), lon_rot.max(), lat_rot.min(), lat_rot.max()],
    transform=ccrs.PlateCarree(),
    origin="lower",
    cmap="viridis",
    norm=LogNorm(vmin=vmin, vmax=vmax)
)

#pcm = ax.pcolormesh(
#    lon_new_grid,
#    lat_new_grid,
#    data_clipped,
#    transform=ccrs.PlateCarree(),
#    cmap='viridis',
#    norm=LogNorm(vmin=vmin, vmax=vmax),
#    shading="auto"
#)

# ax.set_xlim(-180, 180)  # outside-view convention
#ax.set_xlim(ax.get_xlim()[::-1])
#
#pcm = ax.pcolormesh(new_lons, new_lats, data_clipped, transform=ccrs.PlateCarree(), 
#                    cmap='viridis', norm=LogNorm(vmin=vmin,vmax=vmax))
#pcm = ax.pcolormesh(new_lons, new_lats, data_clipped, transform=ccrs.PlateCarree(), cmap='viridis', vmax=vmax)
# ax.coastlines()

# --- Plot rotated latitude lines ---
#for lat_idx in np.linspace(0, ny-1, 7, dtype=int):  # pick a few latitudes to show
#    ax.plot(lon_rot_flipped[lat_idx, :], lat_rot[lat_idx, :], 
#            transform=ccrs.PlateCarree(), color='white', lw=0.8, alpha=0.8)

for lat_idx in np.linspace(0, ny-1, 7, dtype=int):
    lon = lon_rot_flipped[lat_idx, :]
    lat = lat_rot[lat_idx, :]

    # wrap longitudes to [-180,180] to avoid huge jumps
    lon_wrapped = ((lon + 180) % 360) - 180

    # find indices where the jump is too big
    jump_idx = np.where(np.abs(np.diff(lon_wrapped)) > 180)[0]

    # include all segments; append first point at the end if no jump (close the loop)
    start = 0
    for idx in np.append(jump_idx, len(lon_wrapped)-1):
        seg_lon = lon_wrapped[start:idx+1]
        seg_lat = lat[start:idx+1]

        # if this segment reaches the end and there was no jump, close the loop
        if idx == len(lon_wrapped)-1 and len(jump_idx) == 0:
            seg_lon = np.append(seg_lon, seg_lon[0])
            seg_lat = np.append(seg_lat, seg_lat[0])

        ax.plot(seg_lon, seg_lat, transform=ccrs.PlateCarree(),
                color='white', lw=0.8, alpha=0.8)
        start = idx + 1

        theta = np.radians(90.0-seg_lat[0])
        phi = np.radians(-1.0*seg_lon[0])
        xyz = [np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi), np.cos(theta) ]
        xyz_inv = rot.inv().apply(xyz)
        lat_orig = np.degrees(np.arcsin(xyz_inv[2]))
        lon_orig = np.degrees(np.arctan2(xyz_inv[1], xyz_inv[0]))
        if not np.isnan(lat_orig):
            lat_lab_1 = round(lat_orig)
        else: 
            lat_lab_1 = ''
    
        # --- add label using original unrotated lat/lon ---
        lon_lab = ((seg_lon[0]+180) % 360) - 180
        print("seg[0] lat", seg_lat[0], lon_lab, lat_lab_1)
     #   ax.text(lon_lab, seg_lat[0], f'{int(lat_lab_1)}°',
     #           transform=ccrs.PlateCarree(), 
     #           color='orange', fontsize=6,
     #           verticalalignment='center', horizontalalignment='right')

#                color="white",
#                fontsize=8,
#                ha="center", va="center",
#                bbox=dict(boxstyle="round,pad=0.15",
#                          fc="black", ec="none", alpha=0.5))
                
        start = idx + 1


# --- Plot rotated longitude lines ---
#for lon_idx in np.linspace(0, nx-1, 13, dtype=int):  # pick a few longitudes
#    ax.plot(lon_rot_flipped[:, lon_idx], lat_rot[:, lon_idx], 
#            transform=ccrs.PlateCarree(), color='white', lw=0.8, alpha=0.8)
#for lon_idx in np.linspace(0, nx-1, 13, dtype=int):
#    lon = lon_rot_flipped[:, lon_idx]
#    lat = lat_rot[:, lon_idx]

    # wrap longitudes into [-180, 180]
#    lon_wrapped = ((lon + 180) % 360) - 180

#    if (lon_idx > 0):
#       ax.plot(lon_wrapped, lat, transform=ccrs.PlateCarree(),
#                color='white', lw=0.8, alpha=0.8)

lon_label = np.linspace(180, -180, nx)
for lon_idx in np.linspace(0, nx-1, 13, dtype=int):
    lon = lon_rot_flipped[:, lon_idx]
    lat = lat_rot[:, lon_idx]

    # wrap to [-180, 180]
    lon_wrapped = ((lon + 180) % 360) - 180

    # find seam crossings
    jump = np.abs(np.diff(lon_wrapped)) > 180

    # indices where we split the line
    split_idx = np.where(jump)[0] + 1

    lon_segments = np.split(lon_wrapped, split_idx)
    lat_segments = np.split(lat, split_idx)

    for lo, la in zip(lon_segments, lat_segments):
        if len(lo) > 1:   # avoid single-point segments
            ax.plot(lo, la,
                    transform=ccrs.PlateCarree(),
                    color="white", lw=0.8, alpha=0.8)

        # --- choose label position (closest to equator if visible) ---
        idx = np.argmin(np.abs(la))   # point nearest 0° lat

        lon_plot = lo[idx]
        lat_plot = la[idx]
        print('lon_plot = ',lon_plot)


        xyz_rot = sph_to_cart(lat_plot, lon_plot)   # returns (3,) or (1,3)
        print(xyz_rot)

        # ensure shape (1,3) for scipy Rotation
        xyz_rot = np.atleast_2d(xyz_rot)
        print(xyz_rot)

    # --- invert rotation ---
        xyz_orig = rot.inv().apply(xyz_rot)

    # --- back to spherical ---
        lat_label = np.degrees(np.arcsin(xyz_orig[0, 2]))
        lon_label = np.degrees(np.arctan2(xyz_orig[0, 1], xyz_orig[0, 0]))
        print('lon_label = ',lon_label)
#        lon_label = (-1.0*lon_label + 180) % 360 - 180
#        print('lon_label (2) = ',lon_label)
        ax.text(lon_plot, lat_plot,
                f"{lon_label:.0f}°",
                transform=ccrs.PlateCarree(),
                color='orange', fontsize=6,
                verticalalignment='bottom', horizontalalignment='right')
        
#                ha="center", va="center",
#                bbox=dict(boxstyle="round,pad=0.15",
#                          fc="black", ec="none", alpha=0.5))

# Add gridlines
#gl = ax.gridlines(draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
#gl.top_labels = False   # Don't draw labels on top
#gl.right_labels = False # Don't draw labels on right
#gl.xlabel_style = {'size': 10, 'color': 'black'}
#gl.ylabel_style = {'size': 10, 'color': 'black'}

#gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
# Choose which sides to draw labels on
#gl.top_labels = False
#gl.right_labels = False
#gl.bottom_labels = True
#gl.left_labels = True

# Optionally format the labels
#gl.xlabel_style = {'size': 10, 'color': 'white'}
#gl.ylabel_style = {'size': 10, 'color': 'white'}

# You can also control tick intervals
#gl.xlocator = plt.FixedLocator(np.arange(-180, 181, 30))  # every 30°
#gl.ylocator = plt.FixedLocator(np.arange(-90, 91, 30))    # every 30°

# Optionally, set specific intervals
#gl.xlocator = plt.MultipleLocator(30)  # every 30° longitude
#gl.ylocator = plt.MultipleLocator(30)  # every 30° latitude

# Add colorbar
plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.05)

#plt.colorbar(pcm, ax=ax)
plt.show()



patch_wcs = WCS(naxis=2)
patch_wcs.wcs.crpix = [nx/2, ny/2]
patch_wcs.wcs.cdelt = [-360/nx, 180/ny]   # deg per pixel
# patch_wcs.wcs.crval = [180, 0]            # center lon, lat
patch_wcs.wcs.crval = [180, 0]            # center lon, lat
patch_wcs.wcs.ctype = ["GLON-CAR", "GLAT-CAR"]

patch_header = patch_wcs.to_header()

# 3️⃣ Create a base map (destination grid)

# For example a Mollweide all-sky grid:

nx_base, ny_base = 720, 360

base_wcs = WCS(naxis=2)
base_wcs.wcs.crpix = [nx_base/2, ny_base/2]
base_wcs.wcs.cdelt = [-360/nx_base, 180/ny_base]
base_wcs.wcs.crval = [180, 0]
base_wcs.wcs.ctype = ["GLON-MOL", "GLAT-MOL"]

base_header = base_wcs.to_header()
base_data = np.full((ny_base, nx_base), np.nan)

# Apply your map_patch

#out, footprint = map_patch(
#    base_data, base_header,
#    data, patch_header,
#    method="nearest"
#    method = "bilinear"
#)

out, footprint = map_patch(
    data_rot, base_header,
    data_rot, patch_header,
#    method="nearest",
    method = "bilinear"
)
#data_rot


# simple image view

#plt.imshow(out, origin="lower")
#plt.colorbar(label="Flux")
#plt.title("Reprojected Map")
#plt.show()

# sky projection 

fig = plt.figure(figsize=(20,10))
ax = plt.subplot(projection=base_wcs)
#fig, ax = plt.subplots(subplot_kw={'projection': ccrs.Mollweide()})


#threshold = 10.0
#out_masked = np.where(out < threshold, np.nan, out)

threshold = 0.0

# Mask values below threshold
out_masked = np.ma.masked_less(out, threshold)

out_clamped = np.copy(out)
out_clamped[out_clamped < threshold] = threshold

#im = ax.imshow(out_clamped, origin="lower", norm=LogNorm(vmin=threshold, vmax=300), cmap="viridis")
im = ax.imshow(out_clamped, origin="lower", vmin=threshold, vmax=100, cmap="viridis")
cbar = plt.colorbar(im, ax=ax)
#cbar.set_label("Intensity")

# Binary mask
#mask = (out > threshold).astype(float)

#out_smooth = gaussian_filter(out, sigma=1)  # adjust sigma
#im = ax.imshow(out_smooth, origin="lower", norm=LogNorm(vmin=0.1, vmax=300))


# Smooth the mask
#mask_smooth = gaussian_filter(mask, sigma=1.5)

# Apply as weights
#out_soft = out * mask_smooth



#out_masked = np.where(out_soft < threshold, np.nan, out)

#im = ax.imshow(out, origin="lower", norm=LogNorm(vmin=0.1, vmax=300)  )

#out_plot = gaussian_filter(out, 1.0)

#im = ax.imshow(out_plot, origin="lower")

ny, nx = out.shape
y, x = np.mgrid[:ny, :nx]

lon, lat = base_wcs.wcs_pix2world(x, y, 0)

#im = ax.pcolormesh(
#    lon, lat, out,
#    shading="auto",   # key to remove cell borders
#    transform=ax.get_transform("world")
#)

#plt.colorbar(im, ax=ax)

# im = ax.imshow(out, origin="lower", )

# Set grid spacing
lon = ax.coords[0]
lat = ax.coords[1]

lon.set_ticks(spacing=30 * u.deg)
lat.set_ticks(spacing=30 * u.deg)

lon.set_axislabel("Longitude")
lat.set_axislabel("Latitude")


ax.coords.grid(True)
#plt.colorbar(im, ax=ax, label="Flux")
plt.title("Mollweide Projection")
plt.show()

