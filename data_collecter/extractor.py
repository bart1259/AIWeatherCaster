# Data extractor extracts the downloaded data and cleans it up for image generation

# Determines which stations are in range
# Loops over every year
#   Extract yearly tar
#   Trim out unneceasry stations

import re
import os
import csv
import glob
import pandas as pd
import numpy as np

from config import *

# Extracts the zip file of every year
def extract_year(year):
    tar_file = f'{DOWNLOAD_DIR}/{year}.tar.gz'

    extract_folder = EXTRACT_DIR + '/' + str(year)
    # Make extraction folder if not present
    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)

    # Extract
    print(f"Extracting {year}...")
    os.system(f"tar -xf {tar_file} --directory {extract_folder}")
    

# Removes unnecsary station data
def clean_extracted_data(year):
    print(f"Cleaning {year} data...")

    valid_stations = pd.read_csv(STATIONS_META_DATA_FILE, dtype="str")

    station_data = glob.glob(f"{EXTRACT_DIR}/{year}/*.csv")
    for station_file in station_data:
        station_number = re.search(r'(\d*)\.csv$', station_file).group(1)

        if station_number not in valid_stations["STATION"].values:
            # print(f"Removing {station_file}")
            os.remove(station_file)
            continue

# Generates a csv of the valid stations
def gen_stations(year):
    print(f"Generating {STATIONS_META_DATA_FILE} file...")

    # Open a new CSV file
    with open(STATIONS_META_DATA_FILE, 'w+', newline='\n') as stations_file:
        writer = csv.writer(stations_file)

        # Write header
        writer.writerow(["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME"])

        # Get all the station data
        station_data = glob.glob(f"{EXTRACT_DIR}/{year}/*.csv")
        for station in station_data:
            try:
                file = open(station, 'r+')
                reader = csv.reader(file)
                columns = next(reader)
                data = next(reader)
                frame = pd.DataFrame(columns=columns)
                frame.loc[0] = data

                lat = float(frame["LATITUDE"].values[0])
                lon = float(frame["LONGITUDE"].values[0])

                # Find if station is valid
                if lon >= WEST_LON - MARGIN and lon <= EAST_LON + MARGIN and lat >= SOUTH_LAT - MARGIN and lat <= NORTH_LAT + MARGIN:
                    # Save station to CSV file
                    # print(f"Keeping {frame['NAME'].values[0]}")
                    writer.writerow(frame[["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME"]].to_numpy()[0])
            except:
                pass


if __name__ == "__main__":
    # First extract the starting year
    extract_year(START_YEAR)
    # If the file does not exist, generate the station meta data file
    #  from the first year as it will contain all the stations from the
    #  previous years
    if not os.path.exists(STATIONS_META_DATA_FILE):
        gen_stations(START_YEAR)
    else:
        print(f"Using cached {STATIONS_META_DATA_FILE}")
    # Clean the first year data
    clean_extracted_data(START_YEAR)

    for i in range(START_YEAR - 1, END_YEAR - 1, -1):
        extract_year(i)
        clean_extracted_data(i)