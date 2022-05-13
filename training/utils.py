import numpy as np
import glob
from sklearn.preprocessing import normalize
import matplotlib.pyplot as plt
import tensorflow as tf
from scipy import stats

WEST_LON = -125
EAST_LON = -67
NORTH_LAT = 49
SOUTH_LAT = 25
PIXELS_PER_DEGREE = 2

METRICS = {
    0: "Maximum Temperature",
    1: "Minimum Temperature",
    2: "Average Temperature",
    3: "Relative Humidity",
    4: "Sea Level Pressure",
    5: "Wind X Direction",
    6: "Wind Y Direction",
    7: "Wind Speed"
}

def get_metric_name(metric):
    if isinstance(metric, str):
        return metric
    else:
        return METRICS[metric]

def get_metric_index(metric):
    if isinstance(metric, str):
        for key, val in METRICS.items():
            if val == metric:
                return key
    else:
        return metric

def coord_to_index(lat, lon):
    lat_normalized = (lat - SOUTH_LAT) / (NORTH_LAT - SOUTH_LAT)
    lon_normalized = (lon - WEST_LON) / (EAST_LON - WEST_LON)
    lat_index = int(lat_normalized * (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE)
    lon_index = int(lon_normalized * (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE)
    return (lat_index, lon_index)

def index_to_coord(lat_index, lon_index):
    PIXELS_PER_DEGREE = 4
    
    lat_normalized = lat_index / float(NORTH_LAT - SOUTH_LAT) / PIXELS_PER_DEGREE
    lon_normalized = lon_index / float(EAST_LON  -  WEST_LON) / PIXELS_PER_DEGREE
    
    lat = (lat_normalized * (NORTH_LAT - SOUTH_LAT)) + SOUTH_LAT
    lon = (lon_normalized * (EAST_LON  - WEST_LON))  + WEST_LON
    
    return (lat, lon)

# Loads Data frame
def load_data(glob_pattern="daily_image_data/*.npy"):
    daily_data_files = glob.glob(glob_pattern)
    daily_data = []

    for i, day_data in enumerate(daily_data_files):
        if i % 100 == 99:
            print(".", end="")
        daily_data.append(np.load(day_data))

    daily_data = np.asarray(daily_data)
    return daily_data

# Replace all nans with 0s
def replace_nans(data, replace_with=0):
    data = np.nan_to_num(data, 0)
    return data

def normalize(data, wind_special=True):
    maximum = np.nanmax(data, axis=(0,1,2))
    minimum = np.nanmin(data, axis=(0,1,2))

    # Modify normalization
    # Temperature
    maximum[:3] = maximum[:3].max()
    minimum[:3] = minimum[:3].min()

    for i in range(len(maximum)):
        print(".", end="")
        # Scale wind from -0.5 to 0.5
        if (i == 5 or i == 6) and wind_special:
            data[:,:,:,i] = data[:,:,:,i] / 2.
            continue

        data[:,:,:,i] = (data[:,:,:,i] - minimum[i]) / (maximum[i] - minimum[i])
    
    print(".")
    return data

def preview_graph(data, days, lat, lon, metric):
    plt.gcf().set_size_inches(20, 10)
    metric_index = get_metric_index(metric)
    lati, loni = coord_to_index(lat, lon)
    plt.plot(data[:days, lati, loni, metric_index])
    plt.title(f"({lati},{loni}) {get_metric_name(metric)}")

    plt.show()

def split_data(data, split_percent, days=1, spacing=1, make_output_array=False, output_length=1):
    np.random.seed(42)
    data = data.astype(float)
    if days == 1:
        x_data = data[:-1]
        y_data = data[1:]

        # Shuffle data
        p = np.random.permutation(len(x_data))
        x_data = x_data[p]
        y_data = y_data[p]

        split_index = int(len(x_data) * split_percent)
        x_train_data = x_data[:split_index]
        y_train_data = y_data[:split_index]

        x_test_data = x_data[split_index:]
        y_test_data = y_data[split_index:]

        return (x_train_data, y_train_data, x_test_data, y_test_data)
    else:
        data.astype(float)
        in_data = data[:-output_length]
        out_data = data[days:]

        if make_output_array:
            out_data = np.reshape(out_data, (out_data.shape[0], 1, out_data.shape[1], out_data.shape[2], out_data.shape[3]))
        
        x_data = []
        y_data = []
        
        # Assumes days > output_length
        for i in range(0, len(in_data) - days, spacing):
            x_data.append(in_data[i:i+days])
            y_data.append(out_data[i:i+output_length])

            
        x_data = np.array(x_data)
        y_data = np.array(y_data)
        
        p = np.random.permutation(len(x_data))
        x_data = x_data[p]
        y_data = y_data[p]
        
        split_index = int(len(x_data) * split_percent)
        return (x_data[:split_index], y_data[:split_index], x_data[split_index:], y_data[split_index:])

def distributed_loss(y_pred, y_true, distribution_size=20):
    
    total_loss = 0
    mse = tf.keras.losses.MeanSquaredError()
    
    for i in range(0, y_true.shape[0], distribution_size):
        y_true_d = y_true[i:(i+distribution_size)]
        y_pred_d = y_pred[i:(i+distribution_size)]

        loss = mse(y_true_d, y_pred_d).numpy()
        total_loss += loss * (y_true_d.shape[0])
        
    return total_loss

# Returns the MSE loss of the base model given input x and actual data
def get_base_model_mse_loss(x_test, y_true):
    if len(x_test.shape) == 5:
        return distributed_loss(x_test[:,-1,:,:,:], y_true) / x_test.shape[0]
    else:
        return distributed_loss(x_test, y_true) / x_test.shape[0]

# Returns the MSE loss between two data points
def get_mse_loss(y_pred, y_true):
    return distributed_loss(y_pred, y_true) / y_pred.shape[0]

# Returns the MSE loss for a model
def get_model_mse_loss(model, x_test, y_true, batch_size=8):
    y_pred = model.predict(x_test, batch_size=batch_size)
    return distributed_loss(y_pred, y_true) / y_pred.shape[0]

def loss_by_metric(model, x_test, y_true, batch_size=8):
    y_pred = model.predict(x_test, batch_size=batch_size)
    losses = []
    for i in range(y_pred.shape[3]):
        losses.append(distributed_loss(y_pred[:,:,:,i], y_true[:,:,:,i]) / y_pred.shape[0])
    return losses

def loss_by_pixel(model, x_test, y_true, batch_size=8):
    y_pred = model.predict(x_test, batch_size=batch_size)
    
    ret = np.empty((y_pred.shape[1], y_pred.shape[2]))
    
    for y in range(y_pred.shape[1]):
        print(".", end="")
        for x in range(y_pred.shape[2]):
            ret[y,x] = distributed_loss(y_pred[:,y,x,:], y_true[:,y,x,:]) / y_pred.shape[0]
            
    return ret

def standardize(data):
    for channel in range(8):
        if channel == 5 or channel == 6:
            continue
        data[:,:,:,channel] = stats.zscore(data[:,:,:,channel])
    return data