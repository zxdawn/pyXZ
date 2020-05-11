'''
INPUT:
    geo_em.d<domain>
    MEIC input files

OUTPUT:
    wrfchemi_00z_d01: 0 ~ 11 h
    wrfchemi_12z_d01: 12 ~ 23 h

UPDATE:
    Xin Zhang:
       03/13/2020: Basic
       12/04/2020: Add bilinear method and set radius

Steps:
    1. Create WRF area by reading the info of geo* file
    2. Read MEIC nc files and map species to WRF-Chem species
        and assign to self.emi[species]
    3. Resample self.emi to WRF area, write attributes,
        and assign to self.chemi[species]
    4. Export self.chemi to two 12-hour netCDF files.

Currently, this script just supports MOZCART mechanism.
If you want to apply to other mechanisms, you need to edit:
    1. conversion_table_dtype (below);
    2. conversion_table.csv

'''

import logging
import warnings
import os
from calendar import monthrange
from datetime import datetime, timedelta
from glob import glob
from time import strftime

import numpy as np
import pandas as pd
import xarray as xr
from pyresample.bilinear import resample_bilinear
from pyresample.geometry import AreaDefinition, SwathDefinition
from pyresample.kd_tree import resample_custom, resample_nearest
warnings.filterwarnings('ignore', category=RuntimeWarning, append=True)

# Choose the following line for info or debugging:
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# --- input --- #
data_path = '../input_files/'
output_dir = '../output_files/'
domain = 'd01'
resample_method = 'bilinear'  # nearest, bilinear or idw

# emission year
yyyy_emi = 2016
# simulated date
# emissions of any day in the month are same
yyyy = 2019
mm = 7
dd = 25

# ------------- #
conversion_table_dtype = {'MOZCART': str,
                          'CB05': str,
                          'RADM2': str,
                          'SAPRC99': str,
                          'SAPRC07': str,
                          'ALL': str,
                          'WEIGHT': np.float64,
                          'SOLID': np.int,
                          'VOC': np.int,
                          'MW': np.int,
                          }

# Please don't change the following paras
minhour = 0
maxhour = 23
delta = 1  # unit: hour
days = monthrange(yyyy, mm)[1]  # get number of days of the month
chem1 = output_dir+"wrfchemi_00z_d"+domain
chem2 = output_dir+"wrfchemi_12z_d"+domain

wrf_projs = {1: 'lcc',
             2: 'npstere',
             3: 'merc',
             6: 'eqc'
             }


class meic(object):
    def __init__(self, st, et, delta):
        self.get_info()
        self.read_meic()
        self.resample_WRF(st, et, delta)
        self.create_file()

    def get_info(self, ):
        '''
        Read basic info from geo file generated by WPS
            If want to run this on your laptop and care about the space,
            you can use ncks to subset the nc file (we just need attrs)
            ncks -F -d Time,1,,1000 -v Times geo_em.d01.nc geo_em.d01_subset.nc
        ref: https://fabienmaussion.info/2018/01/06/wrf-projection/
        '''
        self.geo = xr.open_dataset(data_path + 'geo_em.'+domain+'.nc')
        attrs = self.geo.attrs
        i = attrs['WEST-EAST_GRID_DIMENSION'] - 1
        j = attrs['SOUTH-NORTH_GRID_DIMENSION'] - 1

        # calculate attrs for area definition
        shape = (j, i)
        radius = (i*attrs['DX']/2, j*attrs['DY']/2)
        self.radius_of_influence = 20000

        # create area as same as WRF
        area_id = 'wrf_circle'
        proj_dict = {'proj': wrf_projs[attrs['MAP_PROJ']],
                     'lat_0': attrs['CEN_LAT'],
                     'lon_0': attrs['CEN_LON'],
                     'lat_1': attrs['TRUELAT1'],
                     'lat_2': attrs['TRUELAT2'],
                     'a': 6370000,
                     'b': 6370000}
        center = (0, 0)
        self.area_def = AreaDefinition.from_circle(area_id,
                                                   proj_dict,
                                                   center,
                                                   radius,
                                                   shape=shape)
        logging.info(f'Area: {self.area_def}')

    def read_meic(self, ):
        '''
        Read MEIC data of different mechanisms
            and convert to species in MOZART
        '''
        # read conversion table
        df = pd.read_csv('./conversion_table.csv',
                         sep=' *, *',  # delete spaces
                         comment='#',
                         engine="python",
                         dtype=conversion_table_dtype)

        # iterate through MEIC mechanisms
        for col in df.columns[1:-4]:
            logging.info('Reading '+col+' mechanism .....')
            if col == 'ALL':
                # choose any col name
                col_path = df.columns[1]
            else:
                col_path = col
            emi_path = data_path+str(yyyy_emi)+'/'+col_path+'/'
            # drop nan values and don't reset index
            #   we need the index in other variables
            species = df[col].dropna()

            for index, spec in enumerate(species):
                # get variables related to desired chemical mechanism
                name = df[df.columns[0]][species.index[index]]
                weight = df['WEIGHT'][species.index[index]]
                mw = df['MW'][species.index[index]]
                solid = df['SOLID'][species.index[index]]
                voc = df['VOC'][species.index[index]]

                logging.info(' '*8+'Map to '+name+' species')
                emi_exist = hasattr(self, 'emi')

                for index_s, s in enumerate(spec.split('+')):
                    logging.info(' '*10+'Reading '+s+' species ....')
                    pattern = emi_path+'*_'+s+'.nc'
                    # len of filelist should be 5 in sequence:
                    #   agriculture, industry, power,
                    #   residential and transportation
                    files = sorted(glob(pattern))
                    # sum all sources for the specific species
                    ds = xr.open_mfdataset(files,
                                           concat_dim='kind',
                                           combine='nested')

                    if not emi_exist:
                        # just read lon/lat once
                        self.calc_area(ds)
                        self.emi = self.get_ds(ds, name, weight,
                                               solid, mw, voc)
                    else:
                        if len(spec) > 1 and index_s > 0:
                            # like spec_a+spec_b+...
                            self.emi[name] += self.get_ds(ds, name,
                                                          weight, solid,
                                                          mw, voc)[name]
                        else:
                            self.emi[name] = self.get_ds(ds, name,
                                                         weight, solid,
                                                         mw, voc)[name]

                logging.debug(' '*8 +
                              ' min: ' + str(self.emi[name].min().values) +
                              ' max: ' + str(self.emi[name].max().values) +
                              ' mean ' + str(self.emi[name].mean().values)
                              )

    def calc_area(self, ds):
        '''
        Get the lon/lat and area (m2)of emission gridded data
        '''
        ds = ds.isel(kind=0)
        self.emi_lon_b = np.arange(ds['x_range'][0],
                                   ds['x_range'][1]+ds['spacing'][0],
                                   ds['spacing'][0])
        self.emi_lat_b = np.arange(ds['y_range'][0],
                                   ds['y_range'][1]+ds['spacing'][1],
                                   ds['spacing'][1])
        self.emi_lon = (self.emi_lon_b[:-1] + self.emi_lon_b[1:])/2
        self.emi_lat = (self.emi_lat_b[:-1] + self.emi_lat_b[1:])/2

        # ref: https://github.com/Timothy-W-Hilton/STEMPyTools
        lon_bounds2d, lat_bounds2d = np.meshgrid(self.emi_lon_b, self.emi_lat_b)
        EARTH_RADIUS = 6370000.0
        Rad_per_Deg = np.pi / 180.0

        ydim = lon_bounds2d.shape[0]-1
        xdim = lon_bounds2d.shape[1]-1
        area = np.full((ydim, xdim), np.nan)
        for j in range(ydim):
            for i in range(xdim):
                xlon1 = lon_bounds2d[j, i]
                xlon2 = lon_bounds2d[j, i+1]
                ylat1 = lat_bounds2d[j, i]
                ylat2 = lat_bounds2d[j+1, i]

                cap_ht = EARTH_RADIUS * (1 - np.sin(ylat1 * Rad_per_Deg))
                cap1_area = 2 * np.pi * EARTH_RADIUS * cap_ht
                cap_ht = EARTH_RADIUS * (1 - np.sin(ylat2 * Rad_per_Deg))
                cap2_area = 2 * np.pi * EARTH_RADIUS * cap_ht
                area[j, i] = abs(cap1_area - cap2_area) * abs(xlon1 - xlon2) / 360.0

        self.emi_area = area

    def get_ds(self, ds, name, weight, solid, mw, voc):
        '''
        Generate the reshaped ds for species
        '''
        seconds = days*24*3600
        hours = days*24
        # z is the emission of species
        # shape: 5*64000 (kind*grid)
        valid = ds.z != ds.z.attrs['nodata_value']
        if solid:
            # WRF-Chem unit: ug/m3 m/s
            # MEIC: unit: tg/(grid*month)
            ds['z'] = ds['z'].where(valid, 0.) * weight*1e12 \
                      / (seconds * np.tile(self.emi_area.ravel(),
                                           (ds['z'].shape[0], 1)
                                           )
                         )
            ds['z'].attrs['units'] = 'ug/m3 m/s'
        elif voc:
            # WRF-Chem unit: mol km-2 hr-1
            # MEIC unit: 10**6 mol/(grid*month)
            ds['z'] = ds['z'].where(valid, 0.) * weight*1e6 \
                      / (hours*np.tile(self.emi_area.ravel()/1e6,
                                       (ds['z'].shape[0], 1)
                                       )
                         )
            ds['z'].attrs['units'] = 'mol km^-2 hr^-1'
        else:
            # WRF-Chem unit: mol km-2 hr-1
            # MEIC unit: tg/(grid*month)
            ds['z'] = ds['z'].where(valid, 0.) * weight*1e6 \
                      / (hours*mw*np.tile(self.emi_area.ravel()/1e6,
                                          (ds['z'].shape[0], 1)
                                          )
                         )
            ds['z'].attrs['units'] = 'mol km^-2 hr^-1'

        # read hourly factor table
        try:
            # shape: 24*5 (time*kind)
            table = xr.DataArray(np.genfromtxt('./hourly_factor.csv',
                                               delimiter=',',
                                               comments='#',
                                               usecols=(0, 1, 2, 3, 4),
                                               skip_header=2),
                                 dims=['time', 'kind']
                                 )
            table = table/(table.sum(dim='time')/24)

        except OSError:
            logging.info(' '*8 +
                         'hourly_factor.csv does not exist, use 1 instead')
            table = xr.DataArray(np.full((24, 5), 1),
                                 dims=['time', 'kind'])

        # use einsum in xarray to create the hourly emissions
        # https://stackoverflow.com/questions/26089893/understanding-numpys-einsum
        # (24*5) .* (5*64000) = 24* 64000 (time*grid)
        dims = ds['dimension'].values
        ydim = dims[0, 1]
        xdim = dims[0, 0]
        # we need to flip because of the "strange" order
        #   of 1d array in MEIC nc file.
        ds[name] = xr.DataArray(np.flip(table.dot(ds['z']).values.reshape((-1, ydim, xdim)), (1)),
                                dims=['time', 'y', 'x'],
                                attrs=ds['z'].attrs
                                )

        # drop old dims
        ds = ds.drop_dims(['xysize', 'side', 'kind'])
        # create new variables
        lon2d, lat2d = np.meshgrid(self.emi_lon, self.emi_lat)
        lon_bounds2d, lat_bounds2d = np.meshgrid(self.emi_lon_b, self.emi_lat_b)

        # assign to ds
        ds['longitude'] = xr.DataArray(lon2d,
                                       coords=[self.emi_lat, self.emi_lon],
                                       dims=['y', 'x'])
        ds['latitude'] = xr.DataArray(lat2d,
                                      coords=[self.emi_lat, self.emi_lon],
                                      dims=['y', 'x'])

        ds.attrs.pop('title')

        return ds

    def perdelta(self, start, end, delta):
        '''
        Generate the 24-h datetime list
        '''
        curr = start
        while curr <= end:
            yield curr
            curr += delta

    def resample_WRF(self, st, et, delta):
        '''
        Create Times variable and resample emission species DataArray.
        '''
        # generate date every hour
        datetime_list = list(self.perdelta(st, et, timedelta(hours=1)))
        t_format = '%Y-%m-%d_%H:%M:%S'
        # convert datetime to date string
        Times = []
        for timstep in datetime_list:
            times_str = strftime(t_format, timstep.timetuple())
            Times.append(times_str)
        # the method of creating "Times" with unlimited dimension
        # ref: htttps://github.com/pydata/xarray/issues/3407
        Times = xr.DataArray(np.array(Times,
                                      dtype=np.dtype(('S', 19))
                                      ),
                             dims=['Time'])
        self.chemi = xr.Dataset({'Times': Times})

        # resample
        orig_def = SwathDefinition(lons=self.emi['longitude'],
                                   lats=self.emi['latitude'])
        for vname in self.emi.data_vars:
            if 'E_' in vname:
                logging.info(f'Resample {vname} ...')
                resampled_list = []
                for t in range(self.emi[vname].shape[0]):
                    # different resample methods
                    # see: http://earthpy.org/interpolation_between_grids_with_pyresample.html
                    if resample_method == 'nearest':
                        resampled_list.append(resample_nearest(
                                              orig_def,
                                              self.emi[vname][t, :, :].values,
                                              self.area_def,
                                              radius_of_influence=self.radius_of_influence,
                                              fill_value=0.)
                                              )
                    elif resample_method == 'idw':
                        resampled_list.append(resample_custom(
                                              orig_def,
                                              self.emi[vname][t, :, :].values,
                                              self.area_def,
                                              radius_of_influence=self.radius_of_influence,
                                              neighbours=10,
                                              weight_funcs=lambda r: 1/r**2,
                                              fill_value=0.)
                                              )
                    elif resample_method == 'bilinear':
                        resampled_list.append(resample_bilinear(
                                              self.emi[vname][t, :, :].values,
                                              orig_def,
                                              self.area_def,
                                              radius=self.radius_of_influence,
                                              neighbours=10,
                                              nprocs=4,
                                              reduce_data=True,
                                              segments=None,
                                              fill_value=0.,
                                              epsilon=0)
                                              )
                # combine 2d array list to one 3d
                # ref: https://stackoverflow.com/questions/4341359/
                #       convert-a-list-of-2d-numpy-arrays-to-one-3d-numpy-array
                # we also need to flip the 3d array,
                #    because of the "strange" order of 1d array in MEIC nc file
                #    then add another dimension for zdim.
                resampled_data = np.flip(np.rollaxis(np.dstack(resampled_list), -1), 1)[:, np.newaxis, ...]
                # assign to self.chemi with dims
                self.chemi[vname] = xr.DataArray(resampled_data,
                                                 dims=['Time',
                                                       'emissions_zdim',
                                                       'south_north',
                                                       'west_east'
                                                       ]
                                                 )

                # add attrs needed by WRF-Chem
                v_attrs = {'FieldType': 104,
                           'MemoryOrder': 'XYZ',
                           'description': vname,
                           'stagger': '',
                           'coordinates': 'XLONG XLAT',
                           'units': self.emi[vname].attrs['units']
                           }

                self.chemi[vname] = self.chemi[vname].assign_attrs(v_attrs)

                logging.debug(' '*8 +
                              ' min: ' + str(self.chemi[vname].min().values) +
                              ' max: ' + str(self.chemi[vname].max().values) +
                              ' mean ' + str(self.chemi[vname].mean().values)
                              )

    def create_file(self, ):
        '''
        Create two wrfchemi* files:
            wrfchemi_00z_d<n> and wrfchemi_12z_d<n>
        '''
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        comp = dict(zlib=True, complevel=5)
        comp_t = dict(zlib=True, complevel=5, char_dim_name='DateStrLen')
        encoding = {var: comp_t if var == 'Times' else comp
                    for var in self.chemi.data_vars}

        logging.info(f'Saving to {output_dir}wrfchemi_00z_{domain}')
        chemi_00 = self.chemi.isel(Time=np.arange(12)).assign_attrs(self.geo.attrs)
        chemi_00.to_netcdf(
                            output_dir+f'wrfchemi_00z_{domain}',
                            format='NETCDF4',
                            encoding=encoding,
                            unlimited_dims={'Time': True}
                          )

        logging.info(f'Saving to {output_dir}wrfchemi_12z_{domain}')
        chemi_12 = self.chemi.isel(Time=np.arange(12, 24, 1)).assign_attrs(self.geo.attrs)
        chemi_12.to_netcdf(
                            output_dir+f'wrfchemi_12z_{domain}',
                            format='NETCDF4',
                            encoding=encoding,
                            unlimited_dims={'Time': True}
                          )

        logging.info('----- Successfully -----')


if __name__ == '__main__':
    st = datetime(yyyy, mm, dd, minhour)
    et = datetime(yyyy, mm, dd, maxhour)
    meic(st, et, delta)
