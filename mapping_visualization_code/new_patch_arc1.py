import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.spatial.transform import Rotation as R
from matplotlib.colors import LogNorm

PI = np.pi

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

def make_imap_lo_reference_points(rot, option=1):
    if option==1:
        npoints = 4
        lons = np.array([259.200622, 255.499300, 289.800000, 79.200622])
        lats = np.array([5.116296, 34.999941,  -35.600000, -5.116296])
        labels=[ 'Nose', 'V1','V2','Tail']
    if option==2:
        npoints = 7
        lons = np.array([259.200622, 255.499300, 289.800000, 79.200622, 221,150.,0.0 ])
        lats = np.array([5.116296, 34.999941,  -35.600000, -5.116296, 39, 0.0, 0.0])
        labels=[ 'Nose', 'V1','V2','Tail', 'Rcen','Stbd', 'Port']
    if option==3:
        npoints = 10
        lons = np.array([259.200622, 255.499300, 289.800000, 79.200622, 221,150.,0.0, 41, 250.624523, 70.624523])
        lats = np.array([5.116296, 34.999941,  -35.600000, -5.116296, 39, 0.0, 0.0, -39, -41.242979, 41.242979])
        labels=[ 'Nose', 'V1','V2','Tail', 'RibC','Stbd', 'Port','DwnB','ULSR', 'DLSR']


        # --- Reference point in ORIGINAL coordinates ---
    lat_points = np.linspace(0.0,0.0,npoints)
    lon_points = np.linspace(0.0,0.0,npoints)
    for i in range(0,npoints):
        ref_lat = lats[i]     # degrees
        ref_lon = lons[i]     # degrees

    # Convert to xyz
        xyz_ref = np.array([
            np.cos(np.radians(ref_lat)) * np.cos(np.radians(ref_lon)),
            np.cos(np.radians(ref_lat)) * np.sin(np.radians(ref_lon)),
            np.sin(np.radians(ref_lat))
            ])

        # Rotate to map frame
        xyz_ref_rot = rot.apply(xyz_ref)

        # Back to lat/lon in rotated frame
        lat_ref_rot = np.degrees(np.arcsin(xyz_ref_rot[2]))
        lon_ref_rot = -np.degrees(np.arctan2(xyz_ref_rot[1], xyz_ref_rot[0])) # negative sign since we are looking from the inside
        lon_ref_rot = (lon_ref_rot + 180) % 360 - 180   # wrap

        lat_points[i] = lat_ref_rot
        lon_points[i] = lon_ref_rot
        
    return labels, lon_points, lat_points


# --- Load data ---

def make_imap_lo_map(file, lat_center, lon_center, vmin, vmax, output, option=1):

    data = pd.read_csv(file, header=0).values
    ny, nx = data.shape

    # Original grid centers
    lats = np.linspace(-87, 87, ny)
    lons = np.linspace(3, 357, nx)

    # Build corner grid for pcolormesh
    lat_edges = np.linspace(-90, 90, ny+1)
    lon_edges = np.linspace(0, 360, nx+1)
    lon_grid, lat_grid = np.meshgrid(lon_edges, lat_edges)

    # Flatten grid for rotation
    xyz = np.column_stack([
        np.cos(np.radians(lat_grid.ravel())) * np.cos(np.radians(lon_grid.ravel())),
        np.cos(np.radians(lat_grid.ravel())) * np.sin(np.radians(lon_grid.ravel())),
        np.sin(np.radians(lat_grid.ravel()))
    ])

    # --- Rotation ---
    new_colat0, new_lon0 = 90.0 - lat_center, lon_center
    rot = R.from_euler('y', 90-new_colat0, degrees=True) * R.from_euler('z', -new_lon0, degrees=True) 
    xyz_rot = rot.apply(xyz)

    lat_rot = np.degrees(np.arcsin(xyz_rot[:,2])).reshape(ny+1, nx+1)
    lon_rot = np.degrees(np.arctan2(xyz_rot[:,1], xyz_rot[:,0])).reshape(ny+1, nx+1)
    lon_rot = (lon_rot + 180) % 360 - 180

    # For the data
    lon_rot_inside = -lon_rot  # flip longitude

    #lon_edges = compute_edges(lon_rot)
    #lat_edges = compute_edges(lat_rot)

    # --- Plot using pcolormesh ---
    fig, ax = plt.subplots(figsize=(10,5), subplot_kw={'projection': ccrs.Mollweide()})
    ax.set_facecolor('darkblue')

    vmin= vmin
    vmax = vmax
    data_clipped = np.clip(data, vmin, vmax)
    data_filled = np.copy(data_clipped)
    data_filled[np.isnan(data_clipped)] = vmin

    pcm = ax.pcolormesh(lon_rot_inside, lat_rot, data_filled,  # no interpolation!
                        transform=ccrs.PlateCarree(),
                        cmap='viridis', norm=LogNorm(vmin=vmin, vmax=vmax), shading='auto')


    lat_lines = np.linspace(-90, 90, 7)  # every ~30 deg
    for lat0 in lat_lines:
        lon_line = np.linspace(0, 360, nx+1)
        lat_line = np.full_like(lon_line, lat0)

        # Convert to xyz and rotate
        xyz_line = np.column_stack([
            np.cos(np.radians(lat_line)) * np.cos(np.radians(lon_line)),
            np.cos(np.radians(lat_line)) * np.sin(np.radians(lon_line)),
            np.sin(np.radians(lat_line))
        ])
        xyz_line_rot = rot.apply(xyz_line)

        # Back to lat/lon
        lat_rot_line = np.degrees(np.arcsin(xyz_line_rot[:,2]))
        lon_rot_line = -np.degrees(np.arctan2(xyz_line_rot[:,1], xyz_line_rot[:,0]))
        lon_rot_line = (lon_rot_line + 180) % 360 - 180  # wrap to [-180,180]
        # flip for inside view

        # --- Split line wherever jump > 180°
        jump_idx = np.where(np.abs(np.diff(lon_rot_line)) > 180)[0]
        split_idx = np.append(jump_idx, len(lon_rot_line)-1)
        start = 0
        for idx in split_idx:
            seg_lon = lon_rot_line[start:idx+1]
            seg_lat = lat_rot_line[start:idx+1]
            ax.plot(seg_lon, seg_lat, transform=ccrs.PlateCarree(),
                    color='orange', lw=0.8, alpha=0.7)
            start = idx+1


        # pick a tolerance in degrees
            tol = 100.0   # widen if labels disappear

            lon_here = ((seg_lon[0] + 180) % 360) - 180   # ensure [-180,180]

            if abs(lon_here) < tol:   # only near 0° rotated longitude

                theta = np.radians(90.0 - seg_lat[0])
                phi = -np.radians(seg_lon[0])   # inside view sign flip
                phi = np.mod(phi, 2.0*np.pi)

                xyz = [
                    np.sin(theta)*np.cos(phi),
                    np.sin(theta)*np.sin(phi),
                    np.cos(theta)
                ]

                xyz_inv = rot.inv().apply(xyz)

                lat_orig = np.degrees(np.arcsin(xyz_inv[2]))

                if not np.isnan(lat_orig):
                    ax.text(
                        lon_here,
                        seg_lat[0],
                        f"{int(round(lat_orig))}°",
                        transform=ccrs.PlateCarree(),
                        color='orange',
                        fontsize=6,
                        verticalalignment='top',
                        horizontalalignment='right'
                    )

            #theta = np.radians(90.0-seg_lat[0])
            #phi = -np.radians(seg_lon[0]) # sign inversion looking from inside
            #phi = np.mod(phi, 2.0*np.pi)         # wrap to [0, 2π)
            #if (phi > PI):
            #    xyz = [np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi), np.cos(theta) ]
            #    xyz_inv = rot.inv().apply(xyz)
            #    lat_orig = np.degrees(np.arcsin(xyz_inv[2]))
            #    lon_orig = np.degrees(np.arctan2(xyz_inv[1], xyz_inv[0]))
            #    if not np.isnan(lat_orig):
            #        lat_lab_1 = round(lat_orig)
            #    else: 
            #        lat_lab_1 = ''
            #    lon_lab = ((seg_lon[0]+180) % 360) - 180
            #    if lat_lab_1 != '':
    #      ##         lon_lab_inside = -lon_lab
            ##           transform=ccrs.PlateCarree(),
            #          color='orange', fontsize=6,
            #          verticalalignment='center', horizontalalignment='right')


    lon_lines = np.linspace(0, 360, 13)  # every 30 deg
    for lon0 in lon_lines:
        lat_line = np.linspace(-90, 90, ny+1)
        lon_line = np.full_like(lat_line, lon0)

        xyz_line = np.column_stack([
            np.cos(np.radians(lat_line)) * np.cos(np.radians(lon_line)),
            np.cos(np.radians(lat_line)) * np.sin(np.radians(lon_line)),
            np.sin(np.radians(lat_line))
        ])
        xyz_line_rot = rot.apply(xyz_line)

        lat_rot_line = np.degrees(np.arcsin(xyz_line_rot[:,2]))
        lon_rot_line = -np.degrees(np.arctan2(xyz_line_rot[:,1], xyz_line_rot[:,0]))
        lon_rot_line = (lon_rot_line + 180) % 360 - 180
        # flip for inside view

        jump_idx = np.where(np.abs(np.diff(lon_rot_line)) > 180)[0]
        split_idx = np.append(jump_idx, len(lon_rot_line)-1)
        start = 0

        # Find the row closest to 0° rotated latitude
        lat0_idx = np.argmin(np.abs(lat_rot_line))  # lat_rot_line = your rotated lat array for the line

        # Get the corresponding longitude and latitude along that row
        lon_line = lon_rot_line[lat0_idx]
        lat_line = lat_rot_line[lat0_idx]

        for idx in split_idx:
            seg_lon = lon_rot_line[start:idx+1]
            seg_lat = lat_rot_line[start:idx+1]
            ax.plot(seg_lon, seg_lat, transform=ccrs.PlateCarree(),
                    color='orange', lw=0.8, alpha=0.7)
        
            mid_idx = len(seg_lon) // 2 
            lon_plot = seg_lon[mid_idx]
            lat_plot = seg_lat[mid_idx]

            start = idx+1

            xyz_rot = sph_to_cart(lat_plot, lon_plot)   # returns (3,) or (1,3)
            # print(xyz_rot)

            # ensure shape (1,3) for scipy Rotation
            xyz_rot = np.atleast_2d(xyz_rot)
            #    print(xyz_rot)

        # --- invert rotation ---
            xyz_orig = rot.inv().apply(xyz_rot)

        # --- back to spherical ---
            lat_label = np.degrees(np.arcsin(xyz_orig[0, 2]))
            lon_label = np.degrees(np.arctan2(xyz_orig[0, 1], xyz_orig[0, 0]))

            xyz = sph_to_cart(0.0, lon_label)
            xyz_rot_label = rot.apply(xyz)
            lat_plot = np.degrees(np.arcsin(xyz_rot_label[2]))

            print('lon_label = ',lon_label)
    #        lon_label = (-1.0*lon_label + 180) % 360 - 180
    #        print('lon_label (2) = ',lon_label)
            lon_plot = -lon_plot
            if np.abs(lat_label) < 30.0:
                ax.text(lon_plot, lat_plot,
                            f"{lon_label:.0f}°",
                            transform=ccrs.PlateCarree(),
                            color='orange', fontsize=6,
                            verticalalignment='bottom', horizontalalignment='right')

    if (option > 0):

        labels, lon_points, lat_points = make_imap_lo_reference_points(rot, option)
        npoints = len(labels)
        for i in range(0,npoints):
            lon_ref_rot = lon_points[i]
            lat_ref_rot = lat_points[i]
            ref_label = labels[i]
        # --- Plot marker ---
            ax.plot(
                lon_ref_rot,
                lat_ref_rot,
                marker='o',
                markersize=1,
                color='white',
                transform=ccrs.PlateCarree(),
                zorder=5
            )

            # --- Add text ---
            ax.text(
                lon_ref_rot,
                lat_ref_rot,
                f" {ref_label}",
                transform=ccrs.PlateCarree(),
                color='white',
                fontsize=6,
                ha='left',
                va='center',
                zorder=5
            )

    ax.set_xlim(ax.get_xlim()[::-1])

    plt.colorbar(pcm, ax=ax, orientation='horizontal', pad=0.05, label='Flux')
    ax.set_global()
   # plt.show()
    plt.savefig(output, dpi=200, facecolor='w', edgecolor='w', orientation='portrait', format=None, transparent=False, bbox_inches=None, pad_inches=0.1)


file = "map_flux_esa7.csv"
output= "map_flux_esa7.png"
vmin = 1.0
vmax = 200.0
lat_center = 5.0 
lon_center = -105.0
make_imap_lo_map(file, lat_center, lon_center, vmin, vmax, output, option=2)


file = "map_flux_esa6.csv"
output= "map_flux_esa6.png"
vmin = 10.0
vmax = 400.0
lat_center = 5.0 
lon_center = -105.0
make_imap_lo_map(file, lat_center, lon_center, vmin, vmax, output)

file = "map_flux_esa5.csv"
output= "map_flux_esa5.png"
vmin = 40.0
vmax = 600.0
lat_center = 5.0 
lon_center = -105.0
make_imap_lo_map(file, lat_center, lon_center, vmin, vmax, output)
