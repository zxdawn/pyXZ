'''
 INPUT:
    Required:
        IN observation data
        GEBCO terrain data (NetCDF)

 OUTPUT:
    Figure of flight altitude

 UPDATE:
   Xin Zhang:
       08/23/2020: basic
'''

import sys
import xarray as xr
import pandas as pd
from glob import glob
import proplot as plot
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.image as image

sys.path.append('../XZ_maps/')
from xin_cartopy import add_grid, load_province, load_city, load_china_county_level_city


def read_file(file, sheet_name):
    '''Read the flight file'''
    f = pd.read_excel(file, sheet_name=sheet_name)
    # t   = f['CreationTime'].values
    lon = f['Long (deg)'].values
    lat = f['Lat (deg)'].values
    alt = f['Altitude AIMMS (m)'].values/1e3  # km
    Lat_min, Lat_max, Lon_min, Lon_max = lat.min(), lat.max(), lon.min(), lon.max()

    return lon, lat, alt, Lat_min, Lat_max, Lon_min, Lon_max


def plot_terrain(ax, gebco, south, north, west, east,
                 vmin=None, vmax=None, locator=None, shrink=None):
    '''Plot the terrain in the cropped region'''
    crop = (gebco.lat > south) & (gebco.lat < north) & (gebco.lon > west) & (gebco.lon < east)
    gebco_subset = gebco.where(crop, drop=True)

    m = ax.contourf(gebco_subset.coords['lon'],
                    gebco_subset.coords['lat'],
                    gebco_subset['elevation'],
                    vmin=vmin,
                    vmax=vmax,
                    locator=locator,
                    levels=256,
                    cmap='Grays'
                    )

    ax.format(lonlim=(west, east),
              latlim=(south, north),
              labels=True,
              dms=False)

    ax.colorbar(m, loc='r', label='Terrain height (m)', shrink=shrink)


def plot_airline(ax, lon, lat, alt):
    ax.scatter(lon, lat, color=alt,
                marker='o',
                # cmap='magma_r',
                cmap='plasma_r',
                size=1,
                colorbar='b',
                cmap_kw={'left': 0.1},
                vmin=0.5,
                vmax=5,
                levels=256,
                colorbar_kw={'label': 'Altitude (km)', 'locator': 0.5}
                )


flight_1 = './data/0512.xlsx'
flight_2 = './data/1227.xlsx'
sheet_name = 'Sheet1'

# read terrain data
gebco = xr.open_dataset(glob('../XZ_maps/terrain/GEBCO/gebco*.nc')[0])
projection = ccrs.PlateCarree()
provinces = load_province(projection)
city = load_city(projection)
county = load_china_county_level_city(projection)

# plot
fig, axs = plot.subplots(proj=(None, 'pcarree', 'pcarree', 'pcarree'),
                         nrows=2, ncols=2)
axs.format(abc=True, abcloc='ul', abcstyle='(a)', tight=True)

# ----- subplot1 ----- #
ax = axs[0]
plane = './data/plane.jpg'
im = image.imread(plane)
ax.imshow(im)
ax.axis('off')

# --- subplot 2 ---
ax = axs[1]
south = 35; north = 40; west = 112; east = 118
plot_terrain(ax, gebco, south, north, west, east,
             vmin=0, vmax=3000, locator=600, shrink=0.85)
ax.add_feature(provinces, edgecolor='k', linewidth=.2)

ax.plot(114.5, 38.02, 'r*', markersize=5)
ax.text(114.6, 38.02, 'SJZ', color='red', fontsize=10, fontweight='bold')
ax.plot(114.38, 37.2, 'r*', markersize=5)
ax.text(114.5, 37.2, 'XT', color='red', fontsize=10, fontweight='bold')


# --- subplot 3 ---
ax = axs[2]
lon, lat, alt, south, north, west, east = read_file(flight_1, sheet_name)
south = 37.95; north = 38.4; west = 114.4; east = 114.85
ax.add_feature(county, edgecolor='k', linewidth=.2)
plot_terrain(ax, gebco, south, north, west, east,
             vmin=40, vmax=140, locator=20)
plot_airline(ax, lon, lat, alt)

# ax.plot(114.5, 38.02, 'r*', markersize=5)
ax.text(114.6, 38.02, 'SJZ', color='red', fontsize=10, fontweight='bold')

# --- subplot 4 ---
ax = axs[3]
lon, lat, alt, south, north, west, east = read_file(flight_2, sheet_name)
south = 36.5; north = 38.5; west = 113.5; east = 115.5
ax.add_feature(city, edgecolor='k', linewidth=.2)
plot_terrain(ax, gebco, south, north, west, east,
             vmin=0, vmax=2000, locator=500)
plot_airline(ax, lon, lat, alt)

# ax.plot(114.38, 37.2, 'r*', markersize=3)
ax.text(114.5, 37.2, 'XT', color='red', fontsize=10, fontweight='bold')

fig.savefig('./figures/IN_flight.png')
