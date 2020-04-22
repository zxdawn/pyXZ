'''
    INPUT:
        CN radar data
        wrflda* data generated by "create_lda.py"

    OUTPUT:
        Comparison of radar CRF and gridded lightning flashrate
            first row: CRF
            second row: flashrate

    UPDATE:
        Xin Zhang:
            04/22/2020: basic
'''

import sys
import numpy as np
import xarray as xr
import pandas as pd
import proplot as plot
from datetime import datetime
from pyresample.geometry import AreaDefinition

sys.path.append('../XZ_maps')
sys.path.append('../XZ_radar')
sys.path.append('../XZ_model')

from radar import cnradar

wrf_projs = {1: 'lcc',
             2: 'npstere',
             3: 'merc',
             6: 'eqc'
             }

# --- input ---
output_dir = './figures/'
radar_dir = '../XZ_radar/data/Nanjing_20190725/'
radar_list = [
              'Z_RADR_I_Z9250_20190725050100_O_DOR_SA_CAP.bin.bz2',
              'Z_RADR_I_Z9250_20190725050600_O_DOR_SA_CAP.bin.bz2',
              'Z_RADR_I_Z9250_20190725054300_O_DOR_SA_CAP.bin.bz2',
              ]

lda_dir = './data/lda/'
domain = 'd03'
freq_lda = '5min'
extend = [118.5, 119.5, 31.5, 32.5]
lon_d = 0.25
lat_d = 0.25
output_dir = './figures/'

# set the simulation st, et and history freq
time_range = pd.date_range('2019-07-25T00:00:00', '2019-07-25T08:00:00', freq=freq_lda)


def npbytes_to_str(var):
    '''convert bytes to string'''
    return (bytes(var).decode("utf-8"))

def set_axis(radar_list):
    '''set the axis format'''
    f, axs = plot.subplots(proj='eqc',
                           ncols=len(radar_list),
                           nrows=2,
                           span=False,
                           share=3)

    axs.format(rowlabels=['CRF', 'Flashrate'],
               abc=True,
               abcloc='l',
               abcstyle='a)',
               labels=True,
               lonlines=lon_d,
               latlines=lat_d,
               lonlim=(extend[0], extend[1]),
               latlim=(extend[2], extend[3]),
               geogridlinewidth=1,
               geogridcolor='w',
              )

    return axs, f

def get_area(ds_lda):
    '''get the area of lda file'''
    attrs = ds_lda.attrs
    i = attrs['WEST-EAST_GRID_DIMENSION']
    j = attrs['SOUTH-NORTH_GRID_DIMENSION']

    # calculate attrs for area definition
    shape = (j, i)
    radius = (i*attrs['DX']/2, j*attrs['DY']/2)

    # create area as same as WRF
    area_id = 'wrf_circle'
    proj_dict = {'proj': wrf_projs[attrs['MAP_PROJ']],
                 'lat_0': attrs['MOAD_CEN_LAT'],
                 'lon_0': attrs['STAND_LON'],
                 'lat_1': attrs['TRUELAT1'],
                 'lat_2': attrs['TRUELAT2'],
                 'a': 6370000,
                 'b': 6370000}
    center = (0, 0)
    wrf_area = AreaDefinition.from_circle(area_id, proj_dict,
                                          center, radius,
                                          shape=shape)

    return wrf_area

def get_flda(radar_list):
    '''get paired lda files'''
    lda_files = []
    for radar_name in radar_list:
        radar_time = datetime.strptime(radar_name.split('_')[4], '%Y%m%d%H%M%S')
        # https://stackoverflow.com/questions/42264848/
        #      pandas-dataframe-how-to-query-the-closest-datetime-index
        nearest_index = time_range.get_loc(radar_time, method='nearest')
        lda_files.append(time_range[nearest_index].strftime(f'wrflda_{domain}_%Y-%m-%d_%H:%M:%S'))

    return lda_files

# get lda files
lda_files = get_flda(radar_list)

# set axis
axs, f = set_axis(radar_list)

# iterate lda_files, read paired radar data and plot
for f_index, lda_file in enumerate(lda_files):
    ds_lda = xr.open_dataset(lda_dir+lda_file)
    ob_radar = cnradar(radar_dir+radar_list[f_index])
    flashrate = ds_lda['LDACHECK'].sel(Time=0)

    # set paras for radar plot
    levels = np.linspace(-5, 75, 17)
    st = np.datetime_as_string(ob_radar.st, unit='s')
    title = st.replace('T', ' ')

    # plot radar CRF
    ax = axs[f_index]
    m = ax.contourf(ob_radar.crf_lon,
                    ob_radar.crf_lat,
                    ob_radar.crf,
                    cmap='dbz',
                    levels=levels,
                     )
    ax.colorbar(m, loc='r', label='(dBZ)', tickminor=False)
    ax.format(title=title, share=3)

    # set axis for lda plot
    ax = axs[f_index+len(radar_list)]

    # get area
    wrf_area = get_area(ds_lda)
    lda_lon, lda_lat = wrf_area.get_lonlats()
    title = npbytes_to_str(ds_lda['Times'].values)

    # crop flash data
    flashrate = flashrate.where((lda_lon >= extend[0]) &
                                (lda_lon <= extend[1]) &
                                (np.flipud(lda_lat) >= extend[2]) &
                                (np.flipud(lda_lat) <= extend[3]))

    # plot flash rate
    m = ax.pcolormesh(lda_lon,
                      np.flipud(lda_lat),  # flip the latitude
                      flashrate,
                      cmap='YlGnBu_r',
                      )
    ax.colorbar(m, loc='r', label='(#/s)', tickminor=False)
    ax.format(title=title, share=3)

f.savefig('./figures/comp_lda_radar.png')
