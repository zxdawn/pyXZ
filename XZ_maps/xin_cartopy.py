'''
 Functions of maps

 UPDATE:
   Xin Zhang:
       02/17/2020: basic
'''

import platform
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.io.shapereader import Reader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

def add_shape(source, projection):
    return cfeature.ShapelyFeature(Reader(source).geometries(),
                                   projection, facecolor='none')

def add_grid(ax, projection,
            west, east, south, north, lon_d, lat_d,
            xlabels_bottom=True, xlabels_top=False,
            ylabels_left=True, ylabels_right=False,
            xlabel_size=None, ylabel_size=None,
            xlabel_color=None, ylabel_color=None,
            linewidth=0.5, grid_color='k', zorder=3):
    
    ax.set_extent([west, east, south, north], crs=projection)
    gl = ax.gridlines(crs=projection, draw_labels=True,
                      linewidth=linewidth, color=grid_color, linestyle='--', zorder=zorder)

    gl.xlabels_bottom = xlabels_bottom; gl.xlabels_top  = xlabels_top
    gl.ylabels_left   = ylabels_left;  gl.ylabels_right = ylabels_right
    gl.xformatter     = LONGITUDE_FORMATTER
    gl.yformatter     = LATITUDE_FORMATTER
    gl.xlocator       = mticker.FixedLocator(np.arange(west-lon_d, east+lon_d, lon_d))
    gl.ylocator       = mticker.FixedLocator(np.arange(south-lon_d, north+lon_d, lon_d))
    
    if xlabel_size:
        gl.xlabel_style = {'size': xlabel_size}
    if ylabel_size:
        gl.ylabel_style = {'size': ylabel_size}
    if xlabel_color:
        gl.xlabel_color = {'color': xlabel_color}
    if ylabel_color:
        gl.ylabel_color = {'color': ylabel_color}

def load_china(projection=ccrs.PlateCarree()):
    if platform.system() == 'Windows':
        source = 'D:/Github/pyXZ/XZ_maps/shapefiles/cnmap/china_country.shp'

    return add_shape(source, projection)

def load_simplified_china(projection=ccrs.PlateCarree()):
    if platform.system() == 'Windows':
        source = 'D:/Github/pyXZ/XZ_maps/shapefiles/cnmap/simplied_china_country.shp'

    return add_shape(source, projection)

def load_province(projection=ccrs.PlateCarree()):
    if platform.system() == 'Windows':
        source = 'D:/Github/pyXZ/XZ_maps/shapefiles/cnmap/china_province.shp'

    return add_shape(source, projection)

def load_city(projection=ccrs.PlateCarree()):
    if platform.system() == 'Windows':
        source = 'D:/Github/pyXZ/XZ_maps/shapefiles/cnmap/china_city.shp'

    return add_shape(source, projection)

def load_china_county_level_city(projection=ccrs.PlateCarree()):
    if platform.system() == 'Windows':
        source = 'D:/Github/pyXZ/XZ_maps/shapefiles/cnmap/china_county-level_city.shp'

    return add_shape(source, projection)

def load_china_nine_dotted_line(projection=ccrs.PlateCarree()):
    if platform.system() == 'Windows':
        source = 'D:/Github/pyXZ/XZ_maps/shapefiles/cnmap/china_nine_dotted_line.shp'

    return add_shape(source, projection)