'''
INPUT:
    EMC data:
        china_sites_<>
    MEIC input files

OUTPUT:
    One figure of the comparison between
        EMC and WRF-Chem simulation

UPDATE:
    Xin Zhang:
       03/19/2020: Basic

Steps:
    1. Read EMC and WRF-Chem data
    2. Pair these data based on location and datetime
    3. Plot comparisons

Currently, this script just supports four species:
    O3, NO2, CO and SO2
'''

import re
import sys
import numpy as np
import proplot as plot
from wrfchem import read_wrf
import pandas as pd
from wrf import ll_to_xy
import xarray as xr

sys.path.append('../XZ_maps')
from xin_cartopy import load_province, add_grid
provinces  = load_province()

# --- input --- #
wrf_path = './data/'
wrf_file = 'wrfout_d01_2019-07-25_00:00:00'
vnames = ['o3','no2','co','so2']
mw = {vnames[0]: 48,
      vnames[1]:46,
      vnames[2]: 28,
      vnames[3]: 64
     }

emc_path = '/yin_raid/xin/github/pyXZ/XZ_model/data/emc/'
station_file = 'station_list.csv'
bad_stations = ['1158A']

output_dir = './figures/comparisons/'
output_name = 'comp_chem_emc.png'

# set crop
station_crop = [118.6, 118.8, 32, 32.2] # lon_min,lon_max, lat_min, lat_max
# station_crop = [lon.min(), lon.max(), lat.min(), lat.max()]
plot_type = 'station' # 'mean' of stations or just 'station'
plot_locs = False # whether plot station locations on map

def get_wrfvars(wrf_path, wrf_file, vnames):
    '''
    Read WRF variables
    '''
    wrf = read_wrf(wrf_path, wrf_file, vnames=vnames+['times'])
    lon = wrf.dv['lon'].values
    lat = wrf.dv['lat'].values
    t = wrf.dv['times']
    wrf_dict = {}
    for vname in vnames:
        wrf_dict[vname] = wrf.dv[vname][:,0,:,:]*1e3 # ppbv

    return wrf, wrf_dict, t

def read_emc(t):
    '''
    Read EMC data
    '''
    # https://stackoverflow.com/questions/25559978/convert-pandas-datetimeindex-to-yyyymmdd-integer
    # in case it's the next day in LT, we extend the end 8 hours
    date_hourly = pd.date_range(t.min().values, t.max().values+pd.Timedelta(hours=8), freq='1H')#, tz='Asia/Shanghai')
    date_list = list(set(np.vectorize(lambda s: s.strftime('%Y%m%d'))(date_hourly.to_pydatetime())))
    emc_files = []
    for date in date_list:
        emc_files.append(emc_path+'china_sites_'+date+'.csv')

    return pd.concat([pd.read_csv(f) for f in emc_files]), date_hourly

def read_station(file, station_crop):
    '''
    Read station locations
    '''
    df = pd.read_csv(file,
                    sep=' *, *',
                    engine='python'
                   )
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    
    # subset to interested region
    df = df[(df['latitude'] >= station_crop[2]) & (df['latitude'] <= station_crop[3])] 
    df = df[(df['longitude'] >= station_crop[0]) & (df['longitude'] <= station_crop[1])]

    return df

def get_emcvars(emc, wrf, stations, bad_stations, vnames, cols, date_hourly):
    '''
    Get variables from emc data
    '''
    emc_dict = {}
    for vname in vnames:
        df = emc[emc.type == vname.upper()][cols]
        # drop "bad" data
        df = df.drop(columns=bad_stations)
        stations = stations[~stations['code'].isin(bad_stations)]
        # get lon/lat of selected stations
        selected = df.columns[2:]
        locs = stations.loc[stations['code'] == selected, ['longitude', 'latitude']].values
        # convert unit to ppb
        df.iloc[:,2:] *= 24.45/mw[vname] # ug -> ppb
        if vname == 'co':
            df.iloc[:,2:] *= 1e3 # mg -> ppb

        # get hourly datetime (UTC)
        df['utc'] = pd.to_datetime(df['date'].astype(str)\
                                   + df['hour'].astype(str).str.zfill(2),
                                   format='%Y%m%d%H') - pd.Timedelta(hours=8)
        # subset to WRF-Chem hours
        df = df[df['utc'].isin(date_hourly[:-8].to_pydatetime())]

        # drop useless columns
        df = df.drop(columns=['date', 'hour']).reset_index(drop=True)

        # set utc as index and transpose to save locs
        df = df.set_index('utc').T

        # get lon/lat and x/y
        df['longitude'] = locs[:, 0]; df['latitude'] = locs[:, 1]
        x_y = ll_to_xy(wrf.ds, df['latitude'], df['longitude']).values
        df['x'] = x_y[0, :]; df['y'] = x_y[1, :]

        # assign to dict
        emc_dict[vname] = df.dropna(axis=0)

    return emc_dict

def pair(emc_dict, wrf_dict):
    '''
    Pair wrf data and emc data
    '''
    for index,key in enumerate(wrf_dict.keys()):
        emc_var = emc_dict[key]
        t_slice = emc_var.columns[2:-2]
        wrf_var = wrf_dict[key].sel(Time=t_slice)
        # get locs from emc DataFrame and subset wrf DataArray
        x = emc_var.loc[:, 'x']
        y = emc_var.loc[:, 'y']
        wrf_var = wrf_var.isel(south_north=xr.DataArray(y),
                               west_east=xr.DataArray(x)
                              )

        #emc_dict[key] =  emc_var.iloc[:, 2:-2]
        wrf_dict[key] = wrf_var

def plot_lines(emc_dict, wrf_dict, stations, type='mean', loc=True):
    '''
    Plot the lines
    '''
    if loc:
        ax_array = [[1,1,2,3],
                    [1,1,4,5]]
        hratios  = (1,1)
        wratios  = (1,1,2,2)
        proj = {1: 'pcarree'}
    else:
        ax_array = [[1,2],
                    [3,4]]
        proj = None; hratios = None; wratios = None

    # set the figure
    f, axs = plot.subplots(ax_array,
                           share=0,
                           tight=True,
                           axheight=3,
                           hratios=hratios,
                           wratios=wratios,
                           proj=proj,
                          )
    axs.format(abc=True, abcloc='ul', abcstyle='(a)',
               grid=False, share=3,
              )
    # rotation of the xaxis labels
    if loc:
        axs[1:].format(xrotation=0)
    else:
        axs.format(xrotation=0)

    if loc:
        # plot the map
        axs[0].add_feature(provinces, edgecolor='k', linewidth=.3)
        tmp_df = emc_dict[list(emc_dict.keys())[0]]
        stations_lon = tmp_df['longitude']
        stations_lat = tmp_df['latitude']

        # plot the stelected stations
        if type == 'mean':
            axs[0].scatter(stations_lon, stations_lat, edgecolors = 'red9', facecolors="None")
        elif type == 'station':
            clist = []
            for cdict in list(plot.Cycle('ggplot')):
                clist.append(cdict['color'])
            axs[0].scatter(stations_lon, stations_lat,
                           c=clist[:len(stations_lon)],
                           cycle=plot.Cycle('ggplot'))

        # crop to the interested region
        axs[0].format(lonlim=(lon.min(), lon.max()),
                  latlim=(lat.min(), lat.max()),
                  labels=True,
                  lonlines=1, latlines=1,
                  title='')
    
    # iterate through vars (no2, o3 ...)
    for pic,key in enumerate(wrf_dict.keys()):
        if loc:
            pic += 1

        # get x/y data
        y_wrf = wrf_dict[key]
        y_emc = emc_dict[key].iloc[:,2:-2].T
        x     = y_wrf.coords['Time']

        # get station codes
        codes = stations[stations['longitude'].\
                    isin(emc_dict[key]['longitude'])]['code'].values

        # plot lines
        if type == 'station':
            y1 = y_emc; y2 = y_wrf
            label_emc = codes; label_wrf = ''
            cycle_emc = 'ggplot'
            cycle_wrf = plot.Cycle('ggplot', dashes=[(1, 0.5)])
            color_emc = None; color_wrf = None
        elif type == 'mean':
            y1 = y_emc.mean(axis=1); y2 = y_wrf.mean('dim_0')
            label_emc = 'OBS'; label_wrf = 'WRF-Chem'
            cycle_emc = None; cycle_wrf = None
            color_emc = 'red9'; color_wrf = 'blue9'
            
        line_emc = axs[pic].plot(x, y1,
                                 cycle=cycle_emc,
                                 color=color_emc,
                                 labels=label_emc
                                )

        line_wrf = axs[pic].plot(x, y2,
                                 cycle=cycle_wrf,
                                 color=color_wrf,
                                 labels=label_wrf
                                )

        # set axis format
        insert_sub = re.search(r"\d", key)
        if insert_sub:
            letter = key.upper()[:insert_sub.start(0)]
            num = f'$_{key[insert_sub.start(0)]}$'
        else:
            letter = key.upper()
            num = ''

        # clean formats and labels
        axs[pic].format(xformatter='%H:%M',
                        xlocator=('hour',range(0,len(x),2)),
                        xminorlocator=('hour',range(0,len(x),1)),
                        xlabel='Hour (UTC)',
                        ylabel=f'{letter}{num} (ppbv)'
                       )

    # legend
    if type == 'station':
        f.legend(line_emc, loc='r', ncols=1)
    elif type == 'mean':
        f.legend((line_emc, line_wrf), loc='r', ncols=1)

    return f

def main():
    # read wrf and emc data
    wrf, wrf_dict, t = get_wrfvars(wrf_path, wrf_file, vnames)
    stations = read_station(emc_path+station_file, station_crop)
    emc, date_hourly = read_emc(t)
    cols = ['date','hour']+stations['code'].tolist()
    emc_dict = get_emcvars(emc, wrf, stations, bad_stations, vnames, cols, date_hourly)

    # get stations' lon/lat, in case we need it to plot stations
    station_locs = {}
    for vname in vnames:
        station_locs[vname] = emc_dict[vname].loc[:, ['longitude', 'latitude']].values
        # average values in the same chem grids
        emc_dict[vname] = emc_dict[vname].groupby(['x','y']).mean().reset_index()

    # pair chem and emc data together
    pair(emc_dict, wrf_dict)

    # plot comparisons
    f = plot_lines(emc_dict, wrf_dict, stations, type=plot_type, loc=plot_locs)
    f.savefig(output_dir+output_name)

if __name__ == '__main__':
    main()
