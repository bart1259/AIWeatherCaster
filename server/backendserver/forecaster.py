import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import numpy as np
from keras.models import Sequential
from keras.layers import Conv2D
import matplotlib.pyplot as plt

from .map_builder import get_image
from .utils import apply_mask, df_mask

from os.path import exists

# Returns the n day forecast starting from today
# @param n [integer] the number of days to make the array
def get_forecast(n):

    # Calculate the day to calculate the forcast for
    # Ensure it is a new day in all the continental U.S.
    start_dt = datetime.now(tz=pytz.utc)
    start_dt = start_dt.astimezone(timezone('US/Pacific'))
    
    start_date = start_dt.date()

    # Check cache
    last_file_name = "./data/forecasts/" + str(start_date) + "_" + str(n) + ".npy"
    if exists(last_file_name):
        forecasts = []

        for i in range(1, n + 1):
            file_name = "./data/forecasts/" + str(start_date) + "_" + str(i) + ".npy"
            forecasts.append(np.load(file_name))

        return forecasts

    daily_data = []
    forecasts = []

    cur_date = start_date

    # Get data for last 3 days
    for i in range(3):
        cur_date -= timedelta(days=1)
        daily_data.append(get_image(str(cur_date)))

    daily_data.reverse()
    daily_data = np.array(daily_data)

    # Make n predictions
    for i in range(n):
        print(f"Making prediction {i+1} day(s) ahead of {str(start_date)}")
        new_day = forecast(daily_data[-3:,:,:,:])

        # Add to end of array new day
        daily_data = daily_data.tolist()
        daily_data.append(new_day)
        daily_data = np.array(daily_data)
        
        # Cache
        file_name = "./data/forecasts/" + str(start_date) + "_" + str(i + 1)
        os.makedirs("./data/forecasts/", exist_ok=True) 
        np.save(file_name, new_day)

        forecasts.append(new_day)

    return forecasts


# Returns the next day given the last 3 days
# @param last_3_days [numpy array] of shap 3, 48, 116, 8
def forecast(last_3_days):

    input = np.array([condense(last_3_days)])
    # Preprocess input
    input = normalize(input)
    input = replace_nans(input)

    model = get_model()
    output = model.predict(input)[0]

    # Process input
    apply_mask(output, df_mask)
    output = unnormalize(output)

    return output

global singleton_model
singleton_model = None

# Retrieves the model
def get_model():

    try:
        return singleton_model
    
    except:
        singleton_model = create_model()
        singleton_model.build([None, 48, 116, 24])
        singleton_model.load_weights("./res/prediction_model.h5")
        return singleton_model

# Creates the model
def create_model():

    model = Sequential()
    model.add(Conv2D(256, (35, 35), activation='sigmoid', padding="same"))
    model.add(Conv2D(256, (19, 19),activation='sigmoid', padding="same"))
    model.add(Conv2D(384, (9, 9),activation='sigmoid', padding="same"))
    model.add(Conv2D(512, (3, 3),activation='sigmoid', padding="same"))
    model.add(Conv2D(8, (1, 1),activation=None, padding="same"))

    model.compile(optimizer='adam',
              loss="mse",
              metrics=["mae"])

    return model

def condense(data):
    (seq_len, height, width, channels) = data.shape
    data = data.transpose(1,2,0,3).reshape(height, width, seq_len * channels)
    return data

# Replace all nans with 0s
def replace_nans(data):
    data = np.nan_to_num(data, 0)
    return data

minimum = [-92.1032913, -92.1032913, -92.1032913, 0.000692325368, 26.5815451, -1., -1.,  0.]
maximum = [132.52376785, 132.52376785, 132.52376785, 100., 31.89179402, 1., 1., 108.47664471]

# Normalize all data
def normalize(data):

    for i in range(len(maximum)):
        data[:,:,:,i] = (data[:,:,:,i] - minimum[i]) / (maximum[i] - minimum[i])
    
    return data

# Unnormalize data
def unnormalize(data):

    for i in range(len(maximum)):
        data[:,:,i] = (data[:,:,i] * (maximum[i] - minimum[i])) + minimum[i]
    
    return data