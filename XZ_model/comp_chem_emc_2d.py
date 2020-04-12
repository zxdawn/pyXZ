'''
INPUT:
    EMC data:
        china_sites_<yyyymmdd>.csv
    WRF-Chem data:
        wrfout*

OUTPUT:
    One figure of the comparison between
        EMC and WRF-Chem simulation

UPDATE:
    Xin Zhang:
       04/12/2020: Basic

Steps:
    1. Read EMC and WRF-Chem data on the same day
    2. Pair these data based on location and time
    3. Plot 2D comparisons

Currently, this script just supports four species:
    O3, NO2, CO and SO2
'''


import re
import sys
sys.path.append('../XZ_maps')

import numpy as np
import xarray as xr
import pandas as pd
import proplot as plot
from wrf import ll_to_xy
from wrfchem import read_wrf
from matplotlib import colors
from xin_cartopy import load_province

provinces = load_province()

# --- input --- #
wrf_path = './data/wrfchem/'
wrf_file = 'wrfout_d01_2019-07-25_05-00-00'
vnames = ['o3', 'no2', 'co', 'so2']
mw = {vnames[0]: 48,
      vnames[1]: 46,
      vnames[2]: 28,
      vnames[3]: 64
      }

vmax = {vnames[0]: 120,
        vnames[1]: 12,
        vnames[2]: 600,
        vnames[3]: 12,
        }

vspace = {vnames[0]: 20,
          vnames[1]: 2,
          vnames[2]: 100,
          vnames[3]: 2,
          }

emc_path = './data/emc/'
station_file = 'station_list.csv'
# optional: put bad station codes in the list
bad_stations = []

output_dir = './figures/comparisons/'
output_name = 'comp_chem_emc_2d.png'


def read_station(file, station_crop):
    '''Read station locations'''
    df = pd.read_csv(file,
                     sep=' *, *',
                     engine='python'
                     )
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')

    # subset to interested region
    df = df[(df['latitude'] >= station_crop[2].values) &
            (df['latitude'] <= station_crop[3].values) &
            (df['longitude'] >= station_crop[0].values) &
            (df['longitude'] <= station_crop[1].values)]

    return df

def get_wrfvars(wrf_path, wrf_file, vnames):
    '''Read WRF variables'''
    wrf = read_wrf(wrf_path, wrf_file, vnames=vnames+['times'])
    t = wrf.dv['times']
    wrf_dict = {}
    for vname in vnames:
        wrf_dict[vname] = wrf.dv[vname].isel(bottom_top=0)*1e3  # ppbv

    return wrf, wrf_dict, t

def get_emcvars(emc, wrf, stations, vnames, cols,
                date_hourly, bad_stations=None):
    '''Get variables from emc data'''
    emc_dict = {}
    for vname in vnames:
        df = emc[emc.type == vname.upper()][cols]

        # drop "bad" data
        if bad_stations:
            df = df.drop(columns=bad_stations)
            stations = stations[~stations['code'].isin(bad_stations)]

        # get lon/lat of selected stations
        selected = df.columns[2:]
        locs = stations.loc[stations['code'] == selected,
                            ['longitude', 'latitude']].values

        # convert unit to ppb
        df.iloc[:, 2:] *= 24.45/mw[vname]  # ug -> ppb
        if vname == 'co':
            df.iloc[:, 2:] *= 1e3  # mg -> ppb

        # get hourly datetime (UTC)
        df['utc'] = pd.to_datetime(df['date'].astype(str) +
                                   df['hour'].astype(str).str.zfill(2),
                                   format='%Y%m%d%H') - pd.Timedelta(hours=8)

        # subset to WRF-Chem hours
        df = df[df['utc'].isin(date_hourly[:-8].to_pydatetime())]

        # drop useless columns
        df = df.drop(columns=['date', 'hour']).reset_index(drop=True)

        # set utc as index and transpose to save locs
        df = df.set_index('utc').T

        # get lon/lat and x/y
        df['longitude'] = locs[:, 0]
        df['latitude'] = locs[:, 1]
        x_y = ll_to_xy(wrf.ds, df['latitude'], df['longitude']).values
        df['x'] = x_y[0, :]
        df['y'] = x_y[1, :]

        # assign to dict
        emc_dict[vname] = df.dropna(axis=0)

    return emc_dict

def read_emc(t):
    '''Read EMC data'''
    # https://stackoverflow.com/questions/25559978/convert-pandas-datetimeindex-to-yyyymmdd-integer
    # in case it's the next day in LT, we extend the end 8 hours
    date_hourly = pd.date_range(t.min().values, t.max().values +
                                pd.Timedelta(hours=8), freq='1H')
    date_list = list(set(np.vectorize(lambda s: s.strftime('%Y%m%d'))
                     (date_hourly.to_pydatetime())))
    emc_files = []
    for date in date_list:
        emc_files.append(emc_path+'china_sites_'+date+'.csv')

    return pd.concat([pd.read_csv(f) for f in emc_files]), date_hourly

def pair(emc_dict, wrf_dict):
    '''Pair wrf data and emc data'''
    for index, key in enumerate(wrf_dict.keys()):
        emc_var = emc_dict[key]
        # t_slice = emc_var.columns[2:-2]
        # wrf_var = wrf_dict[key].sel(Time=t_slice)
        wrf_var = wrf_dict[key]

        # get locs from emc DataFrame and subset wrf DataArray
        x = emc_var.loc[:, 'x']
        y = emc_var.loc[:, 'y']
        wrf_var = wrf_var.isel(south_north=xr.DataArray(y),
                               west_east=xr.DataArray(x)
                               )

        wrf_dict[key] = wrf_var

def plot_distribution(emc_dict, wrf_dict, wrf, stations):
    '''Plot the distribution'''
    # set the figure
    cmap = 'Spectral'
    f, axs = plot.subplots(ncols=2,
                           nrows=int(len(wrf_dict.keys())/2),
                           tight=True,
                           proj='pcarree',
                           )
    axs.format(abc=True, abcloc='ul', abcstyle='(a)')

    # plot the map
    axs.add_feature(provinces, edgecolor='k', linewidth=.3)

    # iterate through vars (no2, o3 ...)
    for index, key in enumerate(wrf_dict.keys()):
        # get x/y data
        y_wrf = wrf_dict[key]
        y_emc = emc_dict[key].iloc[:, 2:-2].T
        x = y_wrf.coords['Time']

        # get the correct var names
        insert_sub = re.search(r"\d", key)
        if insert_sub:
            letter = key.upper()[:insert_sub.start(0)]
            num = f'$_{key[insert_sub.start(0)]}$'
        else:
            letter = key.upper()
            num = ''

        # get specific var
        varname = list(emc_dict.keys())[index]
        tmp_df = emc_dict[varname]
        stations_lon = tmp_df['longitude']
        stations_lat = tmp_df['latitude']
        col = tmp_df.columns[2]

        # plot wrf simulation
        m = axs[index].pcolormesh(wrf.dv['lon'],
                                  wrf.dv['lat'],
                                  wrf.dv[varname].isel(bottom_top=0)*1e3,  # ppbv
                                  cmap=cmap,
                                  vmin=0,
                                  vmax=vmax[varname],
                                  levels=256
                                  )

        # plot station observation
        sca = axs[index].scatter(tmp_df['longitude'],
                                 tmp_df['latitude'],
                                 c=tmp_df[col],
                                 cmap=cmap,
                                 color=256,
                                 vmin=0,
                                 vmax=vmax[varname],
                                 linewidths=1,
                                 edgecolors='k',
                                 )

        # set colorbar
        cb_levels = plot.arange(0, vmax[varname], vspace[varname])
        axs[index].colorbar(m, loc='r', values=cb_levels, label='(ppbv)')
        axs[index].format(title=f'{letter}{num}')

    # get time in string format
    suptitle = pd.to_datetime(wrf_dict[key].coords['Time'].values) \
        .strftime('%Y%m%d %H:%M:%S (UTC)')

    # set axis again
    axs.format(lonlim=(wrf.dv['lon'].min(), wrf.dv['lon'].max()),
               latlim=(wrf.dv['lat'].min(), wrf.dv['lat'].max()),
               labels=True,
               lonlines=1, latlines=1,
               suptitle=suptitle,
               )

    return f

def main():
    # read wrf and emc data
    wrf, wrf_dict, t = get_wrfvars(wrf_path, wrf_file, vnames)

    # in case some are outside, shrink the region by 0.1 degree
    station_crop = [wrf.dv['lon'].min()+0.1,
                    wrf.dv['lon'].max()-0.1,
                    wrf.dv['lat'].min()+0.1,
                    wrf.dv['lat'].max()-0.1]

    # get stations
    stations = read_station(emc_path+station_file, station_crop)

    # get emc data
    emc, date_hourly = read_emc(t)
    cols = ['date', 'hour'] + stations['code'].tolist()
    emc_dict = get_emcvars(emc, wrf, stations,
                           vnames, cols,
                           date_hourly, bad_stations)

    # get stations' lon/lat, in case we need it to plot station scatters
    station_locs = {}
    for vname in vnames:
        station_locs[vname] = emc_dict[vname].loc[:, ['longitude', 'latitude']].values
        # average values in the same chem grids
        emc_dict[vname] = emc_dict[vname].groupby(['x', 'y'])\
                                         .mean().reset_index()

    # pair chem and emc data together
    pair(emc_dict, wrf_dict)

    # plot comparisons
    f = plot_distribution(emc_dict, wrf_dict, wrf, stations)

    # save
    f.savefig(output_dir+output_name)


if __name__ == '__main__':
    main()
