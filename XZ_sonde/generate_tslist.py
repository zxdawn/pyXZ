'''
 INPUT:
    Required:
        IAP Ozondesonde observation csv data edited by XZ
        wrfout*

    Optional:
       geo_em.<domain>.nc

 OUTPUT:
    tslist file for WRF

 UPDATE:
   Xin Zhang:
       02/19/2020: basic
'''

import sys
import collections
from wrf import xy_to_ll, ll_to_xy
import numpy as np
# import dask.array as da
# import matplotlib.pyplot as plt
# from pyresample.ewa import ll2cr
# from pyresample.geometry import SwathDefinition
# from pyresample.bucket import BucketResampler

sys.path.append('../XZ_maps')
sys.path.append('../XZ_model')
from wrfchem import read_wps, read_wrf
from xin_cartopy import load_province, add_grid
from IAP_ozonesonde import read_profile

def sonde_in_wrf_pyresample(profile, wps):
    # ---- !!!!! Pyresample doesn't work well !!!!! ---- #
    # -------------------------------------------------- #
    # Please use the wrfpython to convert directly.
    # reshape to 2d array for `ll2cr`
    lons = profile['lon'].values.reshape(1, profile['lon'].shape[0])
    lats = profile['lat'].values.reshape(1, profile['lat'].shape[0])

    # create dask array, because `bucket` resampler needs that
    lons = da.from_array(lons)
    lats = da.from_array(lats)

    # calculate row and column
    # ll2cr converts swath longitudes and latitudes to grid columns and rows
    # sonde_route = SwathDefinition(lons=lons, lats=lats)
    # points_in_grid, cols, rows = ll2cr(sonde_route, wps.area)
    # print (points_in_grid, cols, rows)

    # calculate counts in grids
    resampler = BucketResampler(wps.area, lons, lats)
    counts = resampler.get_count()

    # quick plot
    # fig, ax = plt.subplots()
    # plt.imshow(counts)
    # plt.colorbar()
    # plt.show()

    # get grid passed by sonde
    wps_lons, wps_lats = wps.area.get_lonlats()
    lat_idx,  lon_idx  = np.where(np.asarray(counts) > 5)
    station_lons       = wps_lons[lat_idx, lon_idx]
    station_lats       = wps_lats[lat_idx, lon_idx]

    return station_lons, station_lats

def sonde_in_wrf(profile, wrf, coords='xy', unique=True):
    '''
    Calculate the sonde location in WRF
    Output: lon/lat and X/Y
    '''

    # convert sonde lon/lat to X/Y
    x_y = ll_to_xy(wrf.ds, profile['lat'], profile['lon']).values

    # check noise X/Y
    counts = collections.Counter(x_y[0])
    noise_x = list(x for x, num in counts.items() if num <= 2)
    # pair together
    x_y = np.stack((x_y[0], x_y[1]), axis=-1)

    if unique:
        # delete duplicated X/Y
        x_y = np.unique(x_y, axis=0)

    # delete noises
    noise_indices = [i for i, x in enumerate(x_y[:, 0]) if x in noise_x]
    x_y = np.delete(x_y, noise_indices, 0)

    if coords == 'xy':
        return  x_y[:, 0], x_y[:, 1]

    elif coords == 'll':
        lat_lon = xy_to_ll(wrf.ds, x_y[:, 0], x_y[:, 1])
        # print (lat_lon)
        # x_y = ll_to_xy(wrf.ds, lat_lon[0], lat_lon[1])
        # print (x_y)

        return lat_lon[0].values, lat_lon[1].values # lat, lon

def generate_tslist(station_lats, station_lons, station_name, pfx_name, coords):
    '''
    Generate the tslist file for WRF running
    Output: tslist content
    '''

    # header and info for WRF tslist
    if coords == 'll':
        header = \
            '#-----------------------------------------------#\n' + \
            '# 24 characters for name | pfx |  LAT  |   LON  |\n' + \
            '#-----------------------------------------------#\n'
    elif coords == 'xy':
        header = \
            '#-----------------------------------------------#\n' + \
            '# 24 characters for name | pfx |   I   |   J   |\n' + \
            '#-----------------------------------------------#\n'

    for i,s in enumerate(station_lats):
        # follow the length principle of tslist
        name  = '{}{:02d}'.format(station_name, i).ljust(26)
        pfx   = '{}{:02d}'.format(pfx_name, i).ljust(7)
        lat_s = str(round(station_lats[i], 3)).ljust(8)
        lon_s = str(round(station_lons[i], 3)).ljust(7)
        header += name + pfx + lat_s + lon_s + '\n'

    return header

def write_tslist(content, filename='tslist.new'):
    with open(filename, "w") as tslist:
        tslist.write(content)

def main():
    # --------------- input --------------- #
    wrf_path = '../XZ_model/data/wrfchem/'
    wrf_file = 'wrfout_d03_2019-07-24_18-00-00'
    sonde = './data/ozonesonde/9_201907251434.txt'
    station_name = 'Jiangning'
    pfx = 'JL'

    # read data and save to tslist for WRF
    # domain = 'd01'
    # wps = read_wps(wrf_path, domain)
    wrf = read_wrf(wrf_path, wrf_file)
    profile, _ = read_profile(sonde, smooth=True)

    # station_lons, station_lats = sonde_in_wrf_pyresample(profile, wps)
    station_lats, station_lons = sonde_in_wrf(profile, wrf, coords='ll')
    content = generate_tslist(station_lats, station_lons, station_name, pfx, coords='ll')

    # write to tslist file as input of WRF TSLIST
    write_tslist(content)


if __name__ == '__main__':
    main()
