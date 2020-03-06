'''
 INPUT:
   Required:
       WRF tslist file:
            <pfx><id>.d<domain>.<variable>

 UPDATE:
   Brian Blaylock:
        12/04/2015: Basic
   
   Xin Zhang:
        02/20/2020: modified for more variables
                    and simplify some codes

Two functions to process data in a TS file outputted by WRF.
get_ts_header reads the header and puts the data in a dictionary.
get_ts_data reads the data and puts a variable in a numpy array.

More information about WRF's tslist can be found in the WRF directory
WRFV3/run/README.tslist
'''

import linecache
import numpy as np

def get_ts_header(TSfile):
    """
    Returns a dictionary with information contined in the header of the TSfile
    produced by WRF.

    Input:
        TSfile - The time series output produced by WRF in the form XXX.d0Y.TS
                 where XXX is the station ID and Y is the domain.
    Output:
        header_dict - A dictionary that contains the following:
            stn_name     = string of the station's full name
            grid_id      = string of the station's ID
            stn_id       = tuple of the station's grid ID
            stn_latlon   = list of the station's real latitude and longitude
            grid_indices = tuple of the grid indices. Location on domain.
            grid_latlon  = list of the grid latitude and longitude
            grid_elev    = float of the grid elevation
            elev_units   = units of the elevation 
    """
    line = linecache.getline(TSfile,1)

    name = line[0:25]
    gridID1 = line[26:29]
    gridID2 = line[29:32]
    stnID = line[33:38]
    stnlat = line[39:46]
    stnlon = line[47:55]
    gridindx1 = line[58:62]
    gridindx2 = line[63:67]
    gridlat = line[70:77]
    gridlon = line[78:86]
    grid_elev = line[88:94]
    elev_units = line[95:]

    header_dict = {'stn_name' : name.strip(),
                   'grid_id' : (int(gridID1), int(gridID2)),
                   'stn_id' : stnID.strip(),
                   'stn_latlon' : [float(stnlat), float(stnlon)],
                   'grid_indices' : (int(gridindx1), int(gridindx2)),
                   'grid_latlon' : [float(gridlat), float(gridlon)],
                   'grid_elev' : float(grid_elev),
                   'elev_units' : elev_units.strip()}

    return header_dict


def get_ts_data(TSfile, variable):
    """
    Opens the tslist output. Packages and returns the data.
    The tslist oupt

    Input:
        TSfile - The time series output produced by WRF in the form XXX.d0Y.TS
                 where XXX is the station ID and Y is the domain number
        variable - The variable in the TSfile you wish to retrieve
            id:          grid ID
            ts_hour:     forecast time in hours
            id_tsloc:    time series ID
            ix,iy:       grid location (nearest grid to the station)
            t:           2 m Temperature (K)
            q:           2 m vapor mixing ratio (kg/kg)
            u:           10 m U wind (earth-relative)
            v:           10 m V wind (earth-relative)
            psfc:        surface pressure (Pa)
            glw:         downward longwave radiation flux at the ground (W/m^2,
                         downward is positive)
            gsw:         net shortwave radiation flux at the ground (W/m^2,
                         downward is positive)
            hfx:         surface sensible heat flux (W/m^2, upward is positive)
            lh:          surface latent heat flux (W/m^2, upward is positive)
            tsk:         skin temperature (K)
            tslb(1):     top soil layer temperature (K)
            rainc:       rainfall from a cumulus scheme (mm)
            rainnc:      rainfall from an explicit scheme (mm)
            clw:         total column-integrated water vapor and cloud
                         variables

    Output:
        A numpy array of the data for the variable you requrested
    """
    # column names as defined by the WRFV3/run/README.tslist
    col_names = ['id', 'ts_hour', 'id_tsloc', 'ix', 'iy', 't', 'q', 'u', 'v',
                 'psfc', 'glw', 'gsw', 'hfx', 'lh', 'tsk', 'tsbl', 'rainc',
                 'rainnc', 'clw']

    # Check that the input variable matches with one in the list.
    if variable not in col_names:
        print ("That variable is not available. Choose a variable from the following list")
        print ("\
        'id'           grid ID\n\
        'ts_hour':     forecast time in hours\n\
        'id_tsloc':    time series ID\n\
        'ix':          grid location (nearest grid to the station)\n\
        'iy':          grid location (nearest grid to the station)\n\
        't':           2 m Temperature (K)\n\
        'q':           2 m vapor mixing ratio (kg/kg)\n\
        'u':           10 m U wind (earth-relative)\n\
        'v':           10 m V wind (earth-relative)\n\
        'psfc':        surface pressure (Pa)\n\
        'glw':         downward longwave radiation flux at the ground (W/m^2, downward is positive)\n\
        'gsw':         net shortwave radiation flux at the ground (W/m^2, downward is positive)\n\
        'hfx':         surface sensible heat flux (W/m^2, upward is positive)\n\
        'lh':          surface latent heat flux (W/m^2, upward is positive)\n\
        'tsk':         skin temperature (K)\n\
        'tslb':        top soil layer temperature (K)\n\
        'rainc':       rainfall from a cumulus scheme (mm)\n\
        'rainnc':      rainfall from an explicit scheme (mm)\n\
        'clw':         total column-integrated water vapor and cloud variables\n\n")

    # Load the file into a numpy array
    TS = np.genfromtxt(TSfile, skip_header=1, names=col_names)

    return TS[variable]


def get_vert_data(TSfile, model_start, get_this_time, model_timestep=2,
                  p_top_requested=5000):
    """
    Gets a vertical profile at a station defined in the tslist at an instant
    defined by get_this_time.
    *Gets the data required to create a sounding.
    *Returns a dictionary that can be used by sounding.py to plot on SkewT
            (*not really yet, need some calculated stuff)

    To use this you have to know something about the timestep of you model
    output. Model_timestep is the timestep in seconds. In my WRF simulations
    I'm using a timestep of 2 seconds in the innermost domain.

    Input:
        TSfile: use the same TS file location as other scripts above. It
                doesn't matter what the last two labels are. We'll strip if off
                and add our own.
        model_start: a datetime object with the start time of the model
        get_this_time: a datetime object with the time step you desire
        model_timestep: the timestep of the model domain in seconds
        p_top_requested: the model top. Used for calculating pressure

    Output:
        The profile UU, VV, TH, PH, QV, P and T
        Also calculated values of wind speed and direction temp and dwpt required
        to make sounding plots.
        UU: U wind
        VV: V wind
        TH: Potential Temperature (K)
        PH: Geopotential Height
        QV: Water Vapor Mixing Ratio
        PR: Pressure (Pa)

    Output (added by Xin):
        The profile O3
        O3: Ozone (ppmv)
    """

    # Figure out which line our desired time is on
    # 1)difference between desired time and model start time
    # 2)how many seconds is between the times?
    # 3)divide by the model timestep = line number the profile is in
    deltaT = get_this_time-model_start
    seconds_from_start = deltaT.seconds+deltaT.days*86400

    # Plus one to account for header row
    row_number = int(seconds_from_start/model_timestep) + 1

    # If the model start and the get time are the same then return the first
    # row time in the model which is really the first time step.
    if model_start == get_this_time:
        print ("called the first time", model_start == get_this_time)
        row_number = 2
    # print ('line:', row_number)

    # Read the line then load into a numpy array
    # (don't return the zeroth column which is just the time)

    vlist = ['UU', 'VV', 'TH', 'PH', 'QV', 'PR', 'O3']
    profile = {}

    for v in vlist:
        tmp = linecache.getline(TSfile[:-2]+v, row_number)
        tmp = np.array(tmp.split(), dtype=float)[1:-2] # omit first and last level
        profile.update({v: tmp})

    return profile
    

def get_full_vert(PROFILEfile, model_start):
    """
    Opens a vertical profile timeseries file and gets all the data.
    PROFILEfile filenames are in the form STATION.d0X.YY where X is the
    domina name and YY is the variable type listed below     
        Available profiles are:
             PH: Geopotential height
             TH: Potential temperature
             QV: Mixing ratio
             UU: U wind
             VV: V wind
    Input:
        PROFILEfile: the file name as listed above
        model_start: a datetime object of the model start time
    Output:
        dates: an array of dates for each timestep
        data: the vertical profile data at each model level. Data has been
              rotated 90 degrees so that top levels are on top of array
              and bottom levels are on bottom of array.
    """

    # Load the file into a numpy array
    raw = np.genfromtxt(PROFILEfile, skip_header=1)

    # convert times to datetime
    raw_dates = raw[:, 0]
    """ # pcolormesh doesn't like dates on the x axis
    dates = np.array([])
    for i in raw_dates:
        dates = np.append(dates, model_start+timedelta(hours=i))
    """
    # get the data and rotate array so that top level is on top and bottom level is on bottom
    data = np.rot90(raw[:, 1:])
    return raw_dates, data
