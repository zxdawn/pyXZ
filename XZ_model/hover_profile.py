'''
INPUT:
    WRF-Chem data:
        wrfout*

OUTPUT:
    Interactively show profiles over hovered grid in pcolormesh

Reference:
    1. https://stackoverflow.com/questions/53446684/
        python-show-corresponding-profile-upon-hovering-clicking-over-a-grid

    2. https://github.com/blaylockbk/pyBKB_v3/blob/master/demo/Nearest_lat-lon_Grid.ipynb

UPDATE:
    Xin Zhang:
       04/23/2020: Basic
'''


# --- input ---
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

wrf_path = './data/wrfchem/'
wrf_file = 'wrfout_d01_2019-07-25_05-00-00'

# choose one mode:
#   button_press_event or motion_notify_event
mode = 'motion_notify_event'

def get_data(f_wrf):
    '''get wrf data'''
    ds = xr.open_dataset(f_wrf)

    da_o3 = ds['o3'].sel(Time=0) * 1e3  # ppbv
    o3_sfc = da_o3.sel(bottom_top=0)
    o3_sfc.attrs['units'] = 'ppbv'

    lon = da_o3.coords['XLONG']
    lat = da_o3.coords['XLAT']

    pressure = (ds['P'] + ds['PB']).sel(Time=0) / 1e2  # hPa

    return lon, lat, da_o3, o3_sfc, pressure

def plot_sfc(ax, lon, lat, o3_sfc):
    '''plot surface o3 on first axis'''
    m = ax.pcolormesh(lon, lat, o3_sfc)

    # set colorbar
    cb = plt.colorbar(m, ax=ax)
    cb.set_label(r'Surface O$_3$ (ppbv)')

    # set title
    ax.set_title(o3_sfc.XTIME.dt.strftime('%Y-%m-%d %H:%M:%S').values)

def hover(event):
    global latlon_idx
    if event.inaxes is ax1:
        # get event location
        event_lat = event.ydata
        event_lon = event.xdata
        # find the absolute value of the difference between
        #   the event's lat/lon with every point in the grid
        abslat = np.abs(lat-event_lat)
        abslon = np.abs(lon-event_lon)
        # takes two arrays and finds the local maximum.
        c = np.maximum(abslon, abslat)
        # find the index location on the grid
        id_grid = np.argmin(c)

        # only plot if we have different values than the previous plot
        if id_grid != latlon_idx:
            # assign the new loc
            latlon_idx = id_grid

            # get the lon and lat of the new grid
            x, y = np.where(c == np.min(c))
            grid_lat = lat[x[0], y[0]]
            grid_lon = lon[x[0], y[0]]

            # clear xis2
            ax2.cla()

            # plot the new profile
            subset = pressure[:, x[0], y[0]] >= 150  # upper limit
            ax2.plot(da_o3[:, x[0], y[0]][subset], pressure[:, x[0], y[0]][subset])

            # set label and title
            ax2.set_ylabel('Pressure (hPa)')
            ax2.set_xlabel('O$_3$ (ppbv)')
            ax2.set_title('O$_3$ profile at \n lat_grid: {:.2f}, lon_grid: {:.2f}'.format(grid_lat.values, grid_lon.values))
            ax2.invert_yaxis()

            fig.canvas.draw_idle()
            fig.tight_layout(h_pad=2)


if __name__ == '__main__':
    # read data
    lon, lat, da_o3, o3_sfc, pressure = get_data(wrf_path+wrf_file)

    # set two axises
    fig, (ax1, ax2) = plt.subplots(2, 1)

    # plot the surface o3 on axis1
    plot_sfc(ax1, lon, lat, o3_sfc)

    # global variables to keep track of which values are currently plotted in ax2
    latlon_idx = None

    cid = fig.canvas.mpl_connect(mode, hover)

    plt.show()
