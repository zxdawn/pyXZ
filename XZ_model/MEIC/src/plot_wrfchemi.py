'''
INPUT:
    wrfchemi_d<domain>

OUTPUT:
    Figures of emission distribution

UPDATE:
    Xin Zhang:
       03/13/2020: Basic
'''

from datetime import datetime

import proplot as plot
import xarray as xr


def npbytes_to_str(var):
    return (bytes(var).decode("utf-8"))


# read data
ds = xr.open_dataset('../output_files/wrfchemi_00z_d01')
# take 06 UTC and 24 MOZCART species as an example
t = 6
# get info of time
Times = ds['Times']
time_str = datetime.strptime("".join(npbytes_to_str(Times[t].values)),
                             "%Y-%m-%d_%H:%M:%S").strftime("%Y-%m-%d_%H:%M:%S")
# get keys except "Times"
species = ds.drop_vars('Times')

# plot
f, axs = plot.subplots(tight=True, share=0,
                       nrows=6, ncols=4,
                       )

axs.format(suptitle=time_str+' nearest')
for index, key in enumerate(species):
    m = axs[index].pcolormesh(ds[key][t, 0, ...], cmap='Fire')
    axs[index].format(title=ds[key].attrs['description'])
    axs[index].colorbar(m, loc='r',
                        label=ds[key].attrs['units'],
                        tickminor=False)

f.savefig('../emission_example.png')
