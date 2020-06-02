import proplot as plot
from glob import glob

f = plot.show_cmaps('aqi', 'dbz', 'pyart_dbz')
f.savefig('cmaps.png')
