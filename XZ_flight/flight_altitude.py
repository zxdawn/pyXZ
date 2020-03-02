'''
 INPUT:
    Required:
        IN observation data

 OUTPUT:
    Figure of flight altitude

 UPDATE:
   Xin Zhang:
       03/02/2020: basic
'''

import sys
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.image as image
import matplotlib.collections as mcoll

sys.path.append('../XZ_maps/')
from xin_cartopy import add_grid, load_province, load_city, load_china_county_level_city

# --------------- set paras --------------- #
file_1 = './data/0512.xlsx'
file_2 = './data/1227.xlsx'
sheet_name = 'Sheet1'

plane  = './data/plane.jpg'
google_map = './data/google_map.png'

save_dir = './'
outputname = 'IN_flight.png'

def add_map(ax, map_data,
              west, east,
              south, north,
              lon_d, lat_d):
    ax.add_feature(map_data, edgecolor='k', linewidth=.2)
    add_grid(ax, ccrs.PlateCarree(),
              west, east,
              south, north,
              lon_d, lat_d,
              xlabel_size=10, ylabel_size=10,
              grid_color='grey')

def read_file(file, sheet_name):
    f   = pd.read_excel(file, sheet_name=sheet_name)
    # t   = f['CreationTime'].values
    lon = f['Long (deg)'].values
    lat = f['Lat (deg)'].values
    alt = f['Altitude AIMMS (m)'].values
    Lat_min, Lat_max, Lon_min, Lon_max = lat.min(), lat.max(), lon.min(), lon.max()

    return lon, lat, alt, Lat_min, Lat_max, Lon_min, Lon_max

def multicolored_lines(ax, lon, lat, alt, cmap, linewidth, alpha):
    """
    http://nbviewer.ipython.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb
    http://matplotlib.org/examples/pylab_examples/multicolored_line.html
    """
    # alt_min = alt.min()
    # alt_max = alt.max()
    # norm = plt.Normalize(vmin=alt_min, vmax=alt_max)
    norm = plt.Normalize(vmin=500, vmax=5000)
    lc = colorline(ax, lon, lat, alt, norm, cmap, linewidth, alpha)
    cbar = plt.colorbar(lc)
    cbar.set_label('Altitude (m)')

def colorline(ax, lon, lat, alt, norm, cmap, linewidth, alpha):
    """
    http://nbviewer.ipython.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb
    http://matplotlib.org/examples/pylab_examples/multicolored_line.html
    Plot a colored line with coordinates x and y
    Optionally specify colors in the array z
    Optionally specify a colormap, a norm function and a line width
    """
    segments = make_segments(lon, lat)
    lc = mcoll.LineCollection(segments, array=alt, cmap=cmap, norm=norm,
                              linewidth=linewidth, alpha=alpha)
    ax.add_collection(lc)

    return lc

def make_segments(x, y):
    """
    Create list of line segments from x and y coordinates, in the correct format
    for LineCollection: an array of the form numlines x (points per line) x 2 (x
    and y) array
    """
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    return segments


def main():
    fig = plt.figure(figsize=[12, 12])
    projection = ccrs.PlateCarree()
    provinces  = load_province(projection)
    city = load_city(projection)
    county = load_china_county_level_city(projection)

    # ----- subplot1 ----- #
    ax = fig.add_subplot(221)
    im = image.imread(plane)
    ax.imshow(im)
    ax.axis('off')
    ax.annotate("(a)", xy=(0.02, 0.93), xycoords="axes fraction")
    ax.set_anchor('W')
    
    # ----- subplot2 ----- #
    ax = fig.add_subplot(222)
    im = image.imread(google_map)
    ax.imshow(im)
    ax.axis('off')
    ax.annotate("(b)", xy=(0.02, 0.93), xycoords="axes fraction")
    ax.set_anchor('W')

    # ----- subplot3 ----- #
    ax = fig.add_subplot(223, projection=projection)
    file = file_1
    sheet_name = 'Sheet1'
    lon, lat, alt, south, north, west, east = read_file(file, sheet_name)
    south = 37.95; north=38.4; west=114.4; east=114.85
    lon_d = 0.1; lat_d = 0.1
    add_map(ax, county, west, east, south, north, lon_d, lat_d)

    im = multicolored_lines(ax, lon, lat, alt, cmap='viridis', linewidth=1, alpha=1)
    ax.plot(114.5, 38.02, 'r*', markersize=10)
    ax.text(114.6, 38.02, 'SJZ', color='red', fontsize=15, fontweight='bold')
    ax.annotate("(c)", xy=(0.02, 0.93), xycoords="axes fraction")
    ax.set_anchor('W')

    # ----- subplot4 ----- #
    ax = fig.add_subplot(224, projection=projection)
    file = file_2
    sheet_name = 'Sheet1'
    lon, lat, alt, south, north, west, east = read_file(file, sheet_name)
    south = 36.5; north=38.5; west=113.5; east=115.5
    lon_d = 0.5; lat_d = 0.5
    add_map(ax, city, west, east, south, north, lon_d, lat_d)

    im = multicolored_lines(ax, lon, lat, alt, cmap='viridis', linewidth=1, alpha=1)
    ax.plot(114.38, 37.2, 'r*', markersize=5)
    ax.text(114.5, 37.2, 'XT', color='red', fontsize=15, fontweight='bold')
    ax.annotate("(d)", xy=(0.02, 0.93), xycoords="axes fraction")
    ax.set_anchor('W')

    plt.show()
    # plt.savefig(save_dir+outputname, bbox_inches='tight')
    # plt.savefig(save_dir+outputname)

if __name__ == '__main__':
    main()