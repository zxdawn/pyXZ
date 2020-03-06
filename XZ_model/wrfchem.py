'''
 Fuctions of WRF-Chem model

 UPDATE:
   Xin Zhang:
       02/18/2020: read geo_em* and create area
       02/19/2020: read wrfout*
'''
import xarray as xr
from netCDF4 import Dataset
from wrf import getvar, ALL_TIMES
from pyresample.geometry import AreaDefinition, SwathDefinition

class read_wps(object):
    def __init__(self, wps_path, domain):
        self.get_info(wps_path, domain)

    def get_info(self, wps_path, domain):
        # read basic info from geo file generrated by WPS
        self.geo = xr.open_dataset(wps_path + 'geo_em.'+domain+'.nc')
        attrs = self.geo.attrs
        # read original attrs
        self.lat_1  = attrs['TRUELAT1']
        self.lat_2  = attrs['TRUELAT2']
        self.lat_0  = attrs['MOAD_CEN_LAT']
        self.lon_0  = attrs['STAND_LON']
        self.cenlat = attrs['CEN_LAT']
        self.cenlon = attrs['CEN_LON']
        self.i      = attrs['i_parent_end']
        self.j      = attrs['j_parent_end']
        self.dx     = attrs['DX']
        self.dy     = attrs['DY']
        self.mminlu = attrs['MMINLU']
        self.map    = attrs['MAP_PROJ']
        self.eta    = attrs['BOTTOM-TOP_GRID_DIMENSION']

        # calculate attrs for area definition
        shape = (self.j, self.i)
        center = (0, 0)
        radius = (self.i*self.dx/2, self.j*self.dy/2)

        # create area as same as WRF
        area_id = 'wrf_circle'
        proj_dict = {'proj': 'lcc', 'lat_0': self.lat_0, 'lon_0': self.lon_0, \
                    'lat_1': self.lat_1, 'lat_2': self.lat_2, \
                    'a':6370000, 'b':6370000}
        self.area = AreaDefinition.from_circle(area_id, proj_dict, center, radius, shape=shape)

class read_wrf(object):
    def __init__(self, wrf_path, fname, vname=None):
        self.get_info(wrf_path, fname, vname)

    def get_info(self, wrf_path, fname, vname):
        # self.wrf = xr.open_dataset(wrf_path+fname)._file_obj.ds
        self.ds = Dataset(wrf_path+fname)
        
        # check vname and read all of them
        self.dv = {}
        if isinstance(vname, str):
            self.dv.update({vname : getvar(self.ds, vname, timeidx=ALL_TIMES)})
        elif isinstance(vname, list):
            for v in vname:
                self.dv.update({vname : getvar(self.ds, v, timeidx=ALL_TIMES)})