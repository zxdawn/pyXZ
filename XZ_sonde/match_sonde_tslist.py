'''
 INPUT:
    Required:
        IAP Ozondesonde observation data
        wrfout* and tslist file

 OUTPUT:
    Save matched profile to txt

 UPDATE:
   Xin Zhang:
       03/06/2020: basic
'''

import sys
import numpy as np
import pandas as pd
from glob import glob
import metpy.calc as mpcalc
from scipy import interpolate
from datetime import datetime, timedelta

sys.path.append('../XZ_model')
from tslist_read import *
from wrfchem import read_wrf
from generate_tslist import sonde_in_wrf
from IAP_ozonesonde import read_profile
from pressure import correct_p

def read_sonde(sonde, p_surf, model_start, step):
    '''
    Read ozonesonde data
    Output: profile dict and timestamps list
    '''

    sonde_profile, _ = read_profile(sonde, smooth=True)
    sonde_profile = sonde_profile.reset_index(drop=True)

    # correct pressures based on GPS and radiosonde
    sonde_profile['PR'][0] = p_surf
    sonde_profile = correct_p(sonde_profile.copy())

    # calculate paired datetime
    sonde_dates = []
    for sonde_date in sonde_profile['t']:
        # if original sonde_date is close to the next step
        # add timedelta to calculated sonde_date
        discard = timedelta(seconds=sonde_date.second%5)#microseconds=sonde_date.microsecond)
        sonde_date -= discard
        if discard >= timedelta(seconds=(step.seconds+1)/2):
            sonde_date += step
        # pair sonde date (default: 1900-01-01) with model date
        #   because the time duration is short enough,
        #   we can just take the model_start as the date
        sonde_dates.append(sonde_date.replace(year=model_start.year, month=model_start.month, day=model_start.day))

    return sonde_profile, sonde_dates

def get_sonde_indices(tslist_path, wrf_path, wrf_file, domain, sonde_profile):
    '''
    Get the indices of sonde in wrf
    Output: X, Y and headers
    '''

    # get headers of all tslists
    headers = {}
    for tslist in glob(tslist_path+'*'+domain+'.TS'):
        grid_indices = get_ts_header(tslist)['grid_indices']
        headers[grid_indices] = tslist

    # get station_indices in model grids
    '''
        You don't need to download the whole big wrfout* file,
        if you're working on your laptop.
        Just subset it using ncks:
        ncks -F -d Time,1,,1000 -v XLONG,XLAT,XTIME,Times wrfout_d01_2019-07-25_00\:00\:00 wrfout_d01_2019-07-25_00_00_00
            where "-F" specificies that the counting begins with 1 as opposed to 0,
                    and every 1000th time record is kept, beginning with the first record.
            Because we just need the head info, use 1000 to subset the initial wrfout* file.
            wrfpython needs XLONG,XLAT,XTIME.
    '''
    wrf = read_wrf(wrf_path, wrf_file, vname=None)
    station_xs, station_ys = sonde_in_wrf(sonde_profile, wrf, coords='xy', unique=False)

    return station_xs, station_ys, headers

def main():
    '''
    Match ozonesonde data with tslist ouput file
    Input:
            tslist file, wrfout*, ozonesonde file
    Output:
            dict of matched profile of h, PR, sonde_O3, QV and O3
            or saved in txt
    '''

    from metpy.units import units
    # --------------- input --------------- #
    # model paras
    wrf_path = '../XZ_model/data/20190725/'
    tslist_path = '../XZ_model/data/20190725/tslist/'
    domain = 'd01'
    wrf_file = 'wrfout_d01_2019-07-25_00_00_00'
    model_start = datetime(2019, 7, 25, 0)
    step = timedelta(seconds=5) # unit: second
    # sonde paras
    sonde = './data/ozonesonde/9_201907251434.txt'
    p_surf = 998.4

    # read data
    sonde_profile, sonde_dates = read_sonde(sonde, p_surf, model_start, step)
    station_xs, station_ys, headers = get_sonde_indices(tslist_path, wrf_path, wrf_file, domain, sonde_profile)

    # get paired profiles
    model_profiles = {}
    for index, station_x in enumerate(station_xs):
        tslist_file = headers[(station_x, station_ys[index])]
        # get vertical data of specific tslist file
        model_profile = get_vert_data(tslist_file, model_start, sonde_dates[index], step.seconds)
        model_profile['O3'] *= 1e3 # ppbv
        model_profile['QV'] *= 1e6 # ppmv
        model_profile['h'] = mpcalc.geopotential_to_height(model_profile['PH'] * 9.80665 * (units.meter ** 2) / (units.second ** 2))

        # assign sonde h, PR and O3 first
        for key in ['h', 'PR', 'O3']:
            if index == 0:
                if key == 'O3':
                    model_profiles['sonde_O3'] = sonde_profile[key][index]
                else:
                    model_profiles[key] = sonde_profile[key][index]
            else:
                if key == 'O3':
                    model_profiles['sonde_O3'] = np.append(model_profiles['sonde_O3'], sonde_profile[key][index])
                else:
                    model_profiles[key] = np.append(model_profiles[key], sonde_profile[key][index])

        # iterate requested model variables in tslists
        for key in ['QV','O3']:
            f = interpolate.interp1d(model_profile['h'], model_profile[key])#, fill_value=np.nan)
            if index == 0:
                model_profiles[key] = f(sonde_profile['h'][index])
            else:
                model_profiles[key] = np.append(model_profiles[key], f(sonde_profile['h'][index]))

    # convert to df and save to txt file
    df = pd.DataFrame.from_dict(model_profiles)
    ouput_name = 'sonde_tslist.txt'
    df.to_csv(ouput_name, sep=',', index=False)

    # add units info
    f = open(ouput_name, "r")
    contents = f.readlines()
    units = 'm,hPa,ppbv,ppmv,ppbv \n' #h,PR,sonde_O3,QV,O3
    contents.insert(1, units)
    f.close()
    
    # write again
    f = open(ouput_name, "w")
    f.writelines(contents)
    f.close()

if __name__ == '__main__':
    main()