# Script that downloads the weather data from the LCD dataset
# The script takes longer to run for more recent years as there is more data

import os
import requests

URL = "https://ncei.noaa.gov/data/local-climatological-data/archive/"

from config import *
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

if __name__ == "__main__":

    for i in range(START_YEAR, END_YEAR - 1, -1):
        # Download file
        print(f"Downloading year {i}...")
        response = requests.request("GET", f"{URL}{i}.tar.gz")

        file_path = f"{DOWNLOAD_DIR}/{i}.tar.gz"

        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded year {i}. Saved to {file_path}")

    print("Done Downloading!") 