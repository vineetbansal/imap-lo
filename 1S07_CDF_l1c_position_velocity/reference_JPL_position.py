
import requests

url = "https://ssd.jpl.nasa.gov/api/horizons.api"

params = {
    "format": "text",
    "COMMAND": "-43",
    "OBJ_DATA": "NO",
    "MAKE_EPHEM": "YES",
    "EPHEM_TYPE": "VECTORS",
    "CENTER": "'500@10'",

    "START_TIME": "'2026-05-13 22:00'",
    "STOP_TIME":  "'2026-05-13 22:01'",
    "STEP_SIZE": "'1 m'",

    "REF_PLANE": "ECLIPTIC",
    "REF_SYSTEM": "J2000",
    "VEC_CORR": "NONE",

    "OUT_UNITS": "AU-D",
    "VEC_TABLE": "2",
}


r = requests.get(url, params=params)
print(r.text)