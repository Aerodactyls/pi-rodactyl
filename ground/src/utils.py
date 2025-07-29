from math import radians, sin, cos, atan2, sqrt
from typing import Tuple, Optional

# typemasks: https://ardupilot.org/dev/docs/copter-commands-in-guided-mode.html#copter-commands-in-guided-mode-set-position-target-global-int
POSITION_TYPEMASK = 0b110111111000
VELOCITY_TYPEMASK = 0b110111000111
YAW_TYPEMASK =      0b100111111111
YAW_RATE_TYPEMASK = 0b010111111111 


def meters_to_feet(meters: float) -> float:
    return meters * 3.28084

def feet_to_meters(feet: float) -> float:
    return feet / 3.28084

def get_lat_lon(position: Tuple[float, float]) -> Tuple[float, float]:
    lat = radians(position[0])
    lon = radians(position[1])
    return (lat, lon)

def distance_two(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    '''
    Return the distance between two points in metres
    Calculated as the great-circle distance using 'haversine’ formula
    (Ref: http://www.movable-type.co.uk/scripts/latlong.html)
    Uses the globally-average earth radius value of 6371km
    '''
    # get_lat_lon_alt returns radians - so no need to convert here
    (lat1, lon1) = get_lat_lon(pos1)
    (lat2, lon2) = get_lat_lon(pos2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1

    a = sin(0.5*dLat)**2 + sin(0.5*dLon)**2 * cos(lat1) * cos(lat2)
    c = 2.0 * atan2(sqrt(a), sqrt(1.0-a))
    ground_dist = 6371 * 1000 * c
    return ground_dist