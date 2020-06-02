import numpy as np
from pycwr.io.auto_io import radar_io


class cnradar(object):
    '''Read CN radar data'''
    def __init__(self, filename, extend=None):
        self.get_data(filename, extend)
        self.get_crf()

    def get_data(self, filename, extend):
        '''Read original data'''
        data = radar_io(filename)
        self.radar = data.ToPRD()
        if extend is None:
            # set extend based on the limit of detection
            lon_min = self.radar.fields[0].lon.min()
            lon_max = self.radar.fields[0].lon.max()
            lat_min = self.radar.fields[0].lat.min()
            lat_max = self.radar.fields[0].lat.max()
        else:
            lon_min, lon_max, lat_min, lat_max = extend

        # set lon/lat
        self.x = np.arange(lon_min, lon_max, 0.01)
        self.y = np.arange(lat_min, lat_max, 0.01)

        # start time
        self.st = self.radar.scan_info['start_time']

    def get_crf(self):
        '''Get CRF data'''
        self.radar.add_product_CR_lonlat(self.x, self.y)
        self.crf = self.radar.product["CR_geo"].values
        self.crf_lon, self.crf_lat = np.meshgrid(self.x, self.y, indexing="ij")
