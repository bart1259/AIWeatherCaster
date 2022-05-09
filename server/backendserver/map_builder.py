# Images of the map are built using https://www.weatherapi.com/
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import time
from tqdm import tqdm
import json
from os.path import exists
import os
import requests

try:
    from .secrets import API_KEY
except:
    print("NO API KET DEFINED! In /backendserver create a secrets.py file with an API key to weatherapi.com\n API_KEY=\"473a...\"")
    exit()


from .utils import filter_nan_gaussian_conserving, coord_to_index, calculate_average_wind, apply_mask, df_mask, GRID_X_SIZE, GRID_Y_SIZE

# Retrieves a 48 x 116 x 8 image for that specified date. If the image has not previously been
# gotten, then the image will be generated
# @param date [string] The date of the requested image
# @param
def get_image(date):
    file_path = f"./data/truth/{date}.npy"

    if exists(file_path):
        return np.load(file_path)

    print(f"Downloading data for {date}")
    os.makedirs("./data/cached_requests/", exist_ok=True)
    image = create_image(date)
    os.makedirs("./data/truth/", exist_ok=True) 
    np.save(file_path, image)
    return image

# Creates the 48 x 116 x 8 daily image snapshot for that date
# @param date [string] date to make the snapshot of (2020-4-21)
# @return a 3d numpy array with the weather data for that day
def create_image(date):
    stations = pd.read_csv("./res/station_data.csv")

    points = []
    values = []

    pbar = tqdm(total=len(stations.index))
    for idx, station in stations.iterrows():
        coords = (station["LATITUDE"], station["LONGITUDE"])
        points.append(coord_to_index(coords[0], coords[1]))
        values.append(get_station_data(coords, date))
        pbar.update(n=1) 


    points = np.array(points)
    values = np.array(values)

    final_image = []

    # Do iterpolation for each channel
    for i in range(values.shape[1]):
        time.sleep(0.5)

        grid_x, grid_y = np.mgrid[0:GRID_X_SIZE, 0:GRID_Y_SIZE]
        interpolated_data = griddata(points, values[:,i], (grid_y, grid_x), method="nearest").T.astype(float)
        apply_mask(interpolated_data, df_mask)
        final_image.append(interpolated_data)

    final_image = np.stack(final_image, axis=2)

    # Blur Each channel
    for i in range(final_image.shape[2]):
        final_image[:,:,i] = filter_nan_gaussian_conserving(final_image[:,:,i], 0.6)

    return final_image

# Retrieves the required about the station from the weather API 
# @param location [tuple] the latitude and longitude to request the data from
# @param date [string] date in the format year-month-day 2020-05-12
# @returns [Array] = [MaxDBTemperature, MinDBTemperature, AvgTemperature, Humidity, Pressure, WindDirectionX, WindDirectionY, WindSpeed]
def get_station_data(location, date):
    day_summary_df = pd.DataFrame.from_dict(json.loads(make_request(location, date))["forecast"]["forecastday"][0]["hour"])
    row = []
    row.append(day_summary_df["temp_f"].max())
    row.append(day_summary_df["temp_f"].min())
    row.append(day_summary_df["temp_f"].mean())
    row.append(day_summary_df["humidity"].mean())
    row.append(day_summary_df["pressure_in"].mean())
    row += calculate_average_wind(day_summary_df["wind_degree"].values, day_summary_df["wind_mph"].values)

    return row

# Makes a request to the weather API
# @param location [tuple] the latitude and longitude to request the data from
# @param date [string] date in the format year-month-day 2020-05-12
def make_request(location, date):
    cache_file_name = f"./data/cached_requests/{date}_{round(location[0], 4)}_{round(location[1], 4)}.txt"
    if exists(cache_file_name):
        file = open(cache_file_name, "r")
        content = file.read()
        file.close()
        return content
    else:
        content = (requests.get(f"http://api.weatherapi.com/v1/history.json?key={API_KEY}&q={location[0]},{location[1]}&dt={date}").content).decode("utf-8") 
        file = open(cache_file_name, "w")
        file.write(content)
        file.close()
        return content


# print(get_image("2022-04-26").shape)