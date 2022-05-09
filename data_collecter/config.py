
START_YEAR = 2021 # Inclusive
END_YEAR = 1990   # Inclusive

# Boundaries
WEST_LON = -125 
EAST_LON = -67
NORTH_LAT = 49
SOUTH_LAT = 25
MARGIN = 1

# How to interpolate the data
INTERPOLATION_STRATEGY="nearest"
# How many pixels per degree if lat or lon
PIXELS_PER_DEGREE = 2
# Should the final result be blurred?
SHOULD_BLUR = True
# How much blurring
SIGMA = 0.6

# Location to download the files
DOWNLOAD_DIR = './downloaded_data'
# Location to extract the files to
EXTRACT_DIR = "./raw_station_data"
# Directory to put all the aggregated data
AGGREGATION_DIR = "./daily_station_data"
# Directory that stores the generated images
DAILY_IMAGE_DIR = "./daily_images"
# Final output directory
FINAL_OUTPUT_DIR = "./final_output"

# File that store station meta data
STATIONS_META_DATA_FILE = "./station_data.csv"
# File for mask
MASK_FILE = "./mask_2.csv"