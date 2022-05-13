# Generates a mask of land and water
# 0s represent oceans and 1s represent land

from mpl_toolkits.basemap import Basemap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import *

if __name__ == "__main__":
    height = (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE
    width = (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE
    print(f"Generating mask of size {width}px wide x {height} tall...")

    data = np.ndarray(shape=(height,width), dtype=float, order='F')
    bm = Basemap(projection='cyl')

    for y in range(0, height):
        for x in range(0, width):
            lat = (y / PIXELS_PER_DEGREE) + SOUTH_LAT
            lon = (x / PIXELS_PER_DEGREE) + WEST_LON
            data[y][x] = 1.0 if bm.is_land(lon, lat) else 0.0
            pass

    pd.DataFrame(data).to_csv(f"mask.csv", index=False, header=False)
    print("Done.")