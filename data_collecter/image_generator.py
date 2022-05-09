# Generates the daily image files the CNN uses as input

from tracemalloc import start
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import glob
import re
from datetime import date, timedelta
import os

from config import *
os.makedirs(DAILY_IMAGE_DIR, exist_ok=True)

start_date = date(START_YEAR, 12, 31)
end_date = date(END_YEAR, 1, 1)

# Calculate sizes
GRID_X_SIZE = (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE
GRID_Y_SIZE = (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE

global current_year_loaded
global station_dfs

current_year_loaded = 0
station_dfs = []

# Load station data for the year
def load_data(year):
    global current_year_loaded
    global station_dfs

    if year == current_year_loaded:
        return station_dfs
    
    print(f"Loading {year}...")
    station_dfs = []
    stations_for_year = glob.glob(AGGREGATION_DIR + "/" + str(year) + "/*.csv")
    for station in stations_for_year:
        station_data = pd.read_csv(station)
        station_number = re.findall(r'(\d*)\.csv$', station)[0]
        station_data["STATION"] = station_number
        station_dfs.append(station_data)
        
    current_year_loaded = year
    return station_dfs

# Load in mask
df_mask = pd.read_csv(MASK_FILE, header=None)
df_mask = df_mask.T

# Function to apply mask
def apply_mask(data, mask):
    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            if (mask[y][x] < 0.5):
                data[y][x] = float('nan')


stations_md = pd.read_csv(STATIONS_META_DATA_FILE, dtype={"STATION":"str","LATITUDE":"float","LONGITUDE":"float"})

# Lattitude is N/S and Longitude is E/W
def get_lat_lon(station_number):
    row = stations_md.loc[stations_md["STATION"] == station_number]
    return (row[["LATITUDE", "LONGITUDE"]].values[0])
    
# Converts a lat lon coordinate to index for grid
def convert_lat_lon_to_index(lat, lon):
    lat_normalized = (lat - SOUTH_LAT) / (NORTH_LAT - SOUTH_LAT)
    lon_normalized = (lon - WEST_LON) / (EAST_LON - WEST_LON)
    lat_index = int(lat_normalized * (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE)
    lon_index = int(lon_normalized * (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE)
    return (lat_index, lon_index)
    
# Function for interploating data on specific date
def interpolate(date, metric):
    # Load data if necessary
    year = int(date.split("-")[0])
    station_dfs = load_data(year)

        
    points = []
    values = []
    for station_data in station_dfs:
        station_number = str(station_data["STATION"][0])

        # Check if date exists
        if (station_data["DATE"] == date).any() :
        
            row = (station_data.loc[(station_data["DATE"] == date)])
            value = row[metric].values[0]
            if math.isnan(value):
                continue
            
            [station_lat, station_lon] = get_lat_lon(station_number)
            index = convert_lat_lon_to_index(station_lat, station_lon)
            points.append([index[0], index[1]])
            values.append(value)

    # Interpolation
    grid_x, grid_y = np.mgrid[0:GRID_X_SIZE, 0:GRID_Y_SIZE]
    
    interpolated_data = griddata(np.array(points), np.array(values), (grid_y, grid_x), method=INTERPOLATION_STRATEGY)
    interpolated_data = interpolated_data.T
    interpolated_data = interpolated_data.astype("float", copy=False)
    
    # Apply Mask
    apply_mask(interpolated_data, df_mask)
    
    return interpolated_data
    
# Interpolates all the data together
def compile_day(date, metrics):
    metric_data = []
    for metric in metrics:
        metric_data.append(interpolate(date, metric).astype(float))
    
    day_summary = np.stack(metric_data, axis=2)
    return day_summary


if __name__ == "__main__":
    # Load in first year
    load_data(START_YEAR)

    # Get metrics
    metrics = station_dfs[0].columns[3:-1]

    delta = start_date - end_date
    for i in range(delta.days + 1):
        day = start_date - timedelta(days=i)
        print(f"Generating image for {str(day)} ...")
        day_data_map = compile_day(str(day), metrics)

        np.save(f"{DAILY_IMAGE_DIR}/{day}_img", day_data_map)