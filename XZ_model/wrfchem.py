'''
 Fuctions of WRF-Chem model

 UPDATE:
   Xin Zhang:
       02/18/2020: read geo_em* and create area
       02/19/2020: read wrfout*
'''
import xarray as xr
from netCDF4 import Dataset
from wrf import getvar, latlon_coords, ALL_TIMES
from pyresample.geometry import AreaDefinition

wrf_projs = {1: 'lcc',
             2: 'npstere',
             3: 'merc',
             6: 'eqc'
             }


class read_wps(object):
    def __init__(self, wps_path, domain):
        self.get_info(wps_path, domain)

    def get_info(self, wps_path, domain):
        # read basic info from geo file generrated by WPS
        self.geo = xr.open_dataset(wps_path + 'geo_em.'+domain+'.nc')
        attrs = self.geo.attrs
        i = attrs['i_parent_end']
        j = attrs['j_parent_end']

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
        self.area_def = AreaDefinition.from_circle(area_id, proj_dict,
                                                   center, radius,
                                                   shape=shape)


class read_wrf(object):
    def __init__(self, wrf_path, fname, vnames=None):
        self.get_info(wrf_path, fname, vnames)

    def get_info(self, wrf_path, fname, vnames):
        # self.wrf = xr.open_dataset(wrf_path+fname)._file_obj.ds
        self.ds = Dataset(wrf_path+fname)

        # check vname and read all of them
        self.dv = {}
        if isinstance(vnames, str):
            self.dv.update({vnames: getvar(self.ds, vnames, timeidx=ALL_TIMES)})
            if vnames != 'Times' and 'lon' not in self.dv:
                self.dv.update({'lat': latlon_coords(self.dv[vnames])[0]})
                self.dv.update({'lon': latlon_coords(self.dv[vnames])[1]})
        elif isinstance(vnames, list):
            for index, v in enumerate(vnames):
                self.dv.update({v: getvar(self.ds, v, timeidx=ALL_TIMES)})
                if v != 'Times' and 'lon' not in self.dv:
                    self.dv.update({'lat': latlon_coords(self.dv[v])[0]})
                    self.dv.update({'lon': latlon_coords(self.dv[v])[1]})

        # get proj
        attrs = xr.open_dataset(wrf_path+fname).attrs
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
        self.area_def = AreaDefinition.from_circle(area_id, proj_dict,
                                                   center, radius,
                                                   shape=shape)
