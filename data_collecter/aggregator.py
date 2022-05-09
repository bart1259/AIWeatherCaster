# Aggregates the stations daily data into hourly summaries

import os
import re
import glob
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
from tqdm import tqdm

from config import *
os.makedirs(AGGREGATION_DIR, exist_ok=True)

# Gets the average wind from historical wind data.
# Averages by adding each vector tip to tail and returning
#  the average direction and magnitude
def get_average_wind(wind_info):
    avg_x = 0
    avg_y = 0
    pts = 0
    for index, row in wind_info.iterrows():
        bearing = row['HourlyWindDirection']
        if not math.isnan(bearing):
            mag = row['HourlyWindSpeed']
            avg_x += -mag * math.sin(math.radians(bearing))
            avg_y += mag * math.cos(math.radians(bearing))
            pts += 1
            
    if pts == 0:
        return (float('nan'),float('nan'),float('nan'))
    else:
        avg_x /= pts
        avg_y /= pts
        mag = math.sqrt((avg_x * avg_x) + (avg_y * avg_y))
        return (avg_x / mag, avg_y / mag, mag)
    
# Aggregates all the information from a day
# x is the daily dataframe
def aggregate_day(x):
    
    avg_xwindbearing, avg_ywindbearing, avg_windspeed = get_average_wind(x[["HourlyWindDirection", "HourlyWindSpeed"]])
    
    ret = pd.DataFrame({
        "DATE":               [x["DATE"].values[0]],
        "Max DBTemperature":  [x["HourlyDryBulbTemperature"].max()],
        "Min DBTemperature":  [x["HourlyDryBulbTemperature"].min()],
        "Avg DBTemperature":  [x["HourlyDryBulbTemperature"].mean()],
        "Avg RelHumidity":    [x["HourlyRelativeHumidity"].mean()],
        "Avg SLPressure":     [x["HourlySeaLevelPressure"].mean()],
        "Avg WindXDirection": [avg_xwindbearing],
        "Avg WindYDirection": [avg_ywindbearing],
        "Avg WindSpeed":      [avg_windspeed],
    })
    # display(ret)
    return ret
    
def remove_time(date_string):
    date_string = re.search(r'^(\d+-\d+-\d+)', date_string).group(1)
    return date_string

# Aggregate a stations hourly data into a daily summary
def aggregate_station(station_file):
    station_data = pd.read_csv (station_file, low_memory=False)
    station_data = station_data[["DATE", "HourlyDryBulbTemperature", "HourlyRelativeHumidity", "HourlySeaLevelPressure", "HourlyWindDirection", "HourlyWindSpeed"]]
    
    # Remove Variable Bearing for wind direction
    station_data.HourlyWindDirection.replace('VRB', float('nan'), inplace=True)
    station_data.HourlyWindDirection.replace('000', float('nan'), inplace=True)
    
    station_data[["HourlyDryBulbTemperature", "HourlyRelativeHumidity", "HourlySeaLevelPressure", "HourlyWindDirection", "HourlyWindSpeed"]] = station_data[["HourlyDryBulbTemperature", "HourlyRelativeHumidity", "HourlySeaLevelPressure", "HourlyWindDirection", "HourlyWindSpeed"]].apply(pd.to_numeric, errors='coerce')
    
    # Remove time from date
    station_data["DATE"] = station_data["DATE"].apply(remove_time)
    
    station_data = station_data.groupby("DATE").apply(aggregate_day)
    return station_data


if __name__ == "__main__":
    for i in range(START_YEAR, END_YEAR - 1, -1):
        print(f"Aggregating hourly data into daily data from {i}... (This might take awhile)")

        # Make dir if it does not exist yet
        os.makedirs(f"{AGGREGATION_DIR}/{i}/", exist_ok=True)

        # Get all station data for year i
        station_data = glob.glob(f"{EXTRACT_DIR}/{i}/*.csv")
        pbar = tqdm(total=len(station_data))
        for station in station_data:
            station_number = re.search(r'(\d*)\.csv$', station).group(1)

            transformed = aggregate_station(station)
            transformed.to_csv(f"{AGGREGATION_DIR}/{i}/_{station_number}.csv")
            pbar.update(n=1)

        print("\n")