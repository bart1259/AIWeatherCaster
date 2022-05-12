import math
import pandas as pd
import numpy as np
from scipy import ndimage

WEST_LON = -125
EAST_LON = -67
NORTH_LAT = 49
SOUTH_LAT = 25
PIXELS_PER_DEGREE = 2

GRID_X_SIZE = (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE
GRID_Y_SIZE = (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE

# Load in mask
MASK_FILE = "./res/mask_2.csv"
df_mask = pd.read_csv(MASK_FILE, header=None)
df_mask = df_mask.T

# Converts a coordinate to an index
# @param lattitude the lattitude value of the point
# @param longitude the longitude value of the point
# @returns the converted index
def coord_to_index(lat, lon):
    lat_normalized = (lat - SOUTH_LAT) / (NORTH_LAT - SOUTH_LAT)
    lon_normalized = (lon - WEST_LON) / (EAST_LON - WEST_LON)
    lat_index = int(lat_normalized * (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE)
    lon_index = int(lon_normalized * (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE)
    return (lat_index, lon_index)

# Calculates the average wind by adding all the wind vectors tip to
# tale and then averaging them
# @param wind_degree an array of the bearing of the wind per hour
# @param wind_speed an array of the wind speed per hour
# @returns [normalized x direction, normalized y direction, average wind speed]
def calculate_average_wind(wind_degree, wind_speed):
    
    wx = 0
    wy = 0
    pts = 0

    for i in range(len(wind_degree)):
        wx += -wind_speed[i] * math.sin(math.radians(wind_degree[i]))
        wy += wind_speed[i] * math.cos(math.radians(wind_degree[i]))
        pts = pts + 1

    wx /= pts
    wy /= pts

    mag = math.sqrt((wx * wx) + (wy * wy))
    return [wx / mag, wy / mag, mag]

# Applies a mask to the data
# If the mask has a 1, the data is kept, if not then it is turned into a nan
# @param data [ndarray] the data to be masked
# @param mask [ndarray] the mask to be applied
# @returns [ndarray] the masked data
def apply_mask(data, mask):
    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            if (mask[y][x] < 0.5):
                data[y][x] = float('nan')


# Applies gausian blur over an array with a given sigma value
# @param arr [ndarray] the array to blur
# @param sigma [number] the blur radius
# @returns the blurred array
def filter_nan_gaussian_conserving(arr, sigma):
    nan_msk = np.isnan(arr)

    loss = np.zeros(arr.shape)
    loss[nan_msk] = 1
    loss = ndimage.gaussian_filter(
            loss, sigma=sigma, mode='constant', cval=1)

    gauss = arr.copy()
    gauss[nan_msk] = 0
    gauss = ndimage.gaussian_filter(
            gauss, sigma=sigma, mode='constant', cval=0)
    gauss[nan_msk] = np.nan

    gauss += loss * arr

    return gauss

# Userd to convert numpy to JSON
def numpy_json_serializer(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type:', type(obj))