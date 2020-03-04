'''
 INPUT:
   Required:
       level l:
           lat: Latitude (degree)
           h: Altitude (h, m)
           t: Temperature (t, degree)
           rh: Relative humidity (rh, %)
        level l-1:
           p_lower: Pressure (hPa)
           h_lower: Altitude (h, m)

 OUTPUT:
   Pressure (hPa) at level l

 UPDATE:
   Xin Zhang:
       02/28/2020: basic version based on Eq. 5 of
                    doi:10.5194/amt-7-65-2014 (R. M. Stauffer)
'''

from scipy.optimize import fsolve, brentq, least_squares
from numpy import sin, sqrt, exp, radians

# constants
G  = 6.67428e-11 # gravitational constant (N m2 kg−2)
Me = 5.9736e24   # mass of Earth (kg)
Re = 6.371e6     # the average radius of Earth (m)
Rd = 287.05      # specific gas constant for dry air (J kg−1 K−1)
Rv = 462         # the specific gas constant for water vapor (J kg-1 K-1)
L  = 2.5e6       # the latent heat of vaporization (J kg-1)
e0 = 6.112       # the vapor pressure at 273.15K (hPa)
TK = 273.15      # 

def calc_p(lat, h, h_lower, t, t_lower, rh, rh_lower, p_lower):
    g_lat = 9.7803267714 * (1+0.00193185138639*(sin(radians(lat)))**2) / sqrt((1-0.00669437999013*(sin(radians(lat)))**2))
    g_h = g_lat + G*Me/(Re+h)**2 - G*Me/Re**2
    # es = e0 * exp(L/Rv*(1/T0 - 1/T))
    # es = e0 * exp((L/Rv)*(1/TK-1/(t+TK)))
    # es_lower = e0 * exp((L/Rv)*(1/TK-1/(t_lower+TK)))
    es = 6.112*(exp(17.67*t/(t+243.5)))
    es_lower = 6.112*(exp(17.67*t_lower/(t_lower+243.5)))

    e = es*(rh/100)
    e_lower = es_lower*(rh_lower/100)

    # Tv = T*(1+0.61*w) = T*(1+0.61*(Rd/Rv)*(e/(p-e)))
    Tv_lower = (t_lower+TK)*(1+0.61*(Rd/Rv)*e_lower/(p_lower-e_lower))

    # Solve equation
    # p = p_lower * exp(-g_h*(h-h_lower) / (Rd*Tv))
    def f(p):
        Tv = (t+TK)*(1+0.61*(Rd/Rv)*e/(p-e))
        return p - p_lower * exp( -g_h*(h-h_lower) / (Rd*(Tv+Tv_lower)/2) )

    p = fsolve(f, p_lower)

    return p
