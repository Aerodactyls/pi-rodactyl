import os
import sys
from functools import reduce
from typing import Dict, Tuple

def pull() -> Dict[str, Tuple[float, float]]:
    dict = {}
    
    doc = open(os.path.expanduser("~") + "/Documents/Mission Planner/poi.txt")

    for line in doc.readlines():
        # splits up by whitespace
        parts = line.split()
        
        # note: there could technically be a waypoint
        # that has no name, then len(parts) == 2
        if len(parts) < 2:
            continue

        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if len(parts) == 2:
                name = ""
            else:
                name = reduce(lambda x, y: x + " " + y, parts[2:])

            dict[name] = (lat, lon)
        except Exception:
            ...

    return dict

def get_numerical_pois(poi_dict: Dict[str, Tuple[float, float]]) -> list[Tuple[float, float]]:
    result = []
    for i in range(12):
        if str(i) in poi_dict:
            result.append(poi_dict[str(i)])
    return result