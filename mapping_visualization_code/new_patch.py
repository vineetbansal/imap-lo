import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.interpolate import griddata
from scipy.spatial.transform import Rotation as R
from matplotlib.colors import LogNorm
from scipy.ndimage import gaussian_filter

# -----------------------------
# Helper functions
# -----------------------------
def sph_to_cart(lat, lon):
    """Convert lat/lon (degrees) to Cartesian xyz"""
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    return np.array([x, y, z])

def rotation_matrix_to_center(new_colat0, new_lon0):
    """
    Rotation matrix to place new_colat0/new_lon0 at north pole.
    """
    r1 = R.from_euler('z', -new_lon0, degrees=True)
    r2 = R.from_euler('y', 90 - new_colat0, degrees=True)
    return r2 * r1

# -----------------------------
# Load data
# -----------------------------
data = pd.read_csv("map_flux_esa7.csv", header=0).values
ny, nx = data.shape

# Original lat/lon grid
lats = np.linspace(-87, 87, ny)
lons = np.linspace(3, 357, nx)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Flatten grid for rotation/interpolation
xyz = sph_to_cart(lat_grid, lon_grid).reshape(3, -1).T

# -----------------------------
# Rotate coordinates
# -----------------------------
new_colat0 = 85   # center latitude for rotation
new_lon0   = -90  # center longitude

rot = rotation_matrix_to_center(new_colat0, new_lon0)
xyz_rot = rot.apply(xyz)

# Convert back to lat/lon
lat_rot = np.degrees(np.arcsin(xyz_rot[:, 2]))
lon_rot = np.degrees(np.arctan2(xyz_rot[:, 1], xyz_rot[:, 0]))

# -----------------------------
# Make longitudes continuous (prevent wrap artifacts)
# -----------------------------
lon_rot_cont = lon_rot.copy()
# Shift so minimum longitude = 0
lon_rot_cont -= lon_rot_cont.min()
lon_rot_cont = lon_rot_cont.reshape(ny, nx)
lat_rot = lat_rot.reshape(ny, nx)

# -----------------------------
# Interpolate onto regular grid
# -----------------------------
target_ny, target_nx = 360, 720  # fine 0.5 deg grid
new_lats = np.linspace(-90, 90, target_ny)
new_lons = np.linspace(0, lon_rot_cont.max(), target_nx)
lon_new_grid, lat_new_grid = np.meshgrid(new_lons, new_lats)

points = np.column_stack((lon_rot_cont.ravel(), lat_rot.ravel()))
values = data.ravel()

# Use linear interpolation
data_interp = griddata(points, values, (lon_new_grid, lat_new_grid),
                       method='linear', fill_value=0.0)

# Optional smoothing
data_smooth = gaussian_filter(data_interp, sigma=1)

# -----------------------------
# Plot
# -----------------------------
vmin, vmax = 10, 160
fig = plt.figure(figsize=(10,5))
ax = fig.add_subplot(1,1,1, projection=ccrs.Mollweide())

# Use imshow to display smoothly
im = ax.imshow(
    data_smooth,
    extent=[0, lon_rot_cont.max(), -90, 90],  # continuous longitudes
    transform=ccrs.PlateCarree(),
    origin='lower',
    cmap='viridis',
    norm=LogNorm(vmin=vmin, vmax=vmax),
    interpolation='nearest'
)

# -----------------------------
# Add rotated grid lines
# -----------------------------
# Select a few latitudes
for lat_idx in np.linspace(0, ny-1, 7, dtype=int):
    lon_line = lon_rot_cont[lat_idx, :]
    lat_line = lat_rot[lat_idx, :]
    ax.plot(lon_line, lat_line, color='white', lw=0.8, alpha=0.7, transform=ccrs.PlateCarree())

# Select a few longitudes
for lon_idx in np.linspace(0, nx-1, 13, dtype=int):
    lon_line = lon_rot_cont[:, lon_idx]
    lat_line = lat_rot[:, lon_idx]
    ax.plot(lon_line, lat_line, color='white', lw=0.8, alpha=0.7, transform=ccrs.PlateCarree())

# -----------------------------
# Colorbar
# -----------------------------
plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.05, label="Flux")
plt.show()
