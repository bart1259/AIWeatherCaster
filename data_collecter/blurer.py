# Script that blurs all images in a directory
import matplotlib.pyplot as plt
from scipy import ndimage
from scipy.ndimage import gaussian_filter
import numpy as np
import glob
import os

from config import *
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

def filter_nan_gaussian_conserving(arr, sigma):
    """Apply a gaussian filter to an array with nans.

    Intensity is only shifted between not-nan pixels and is hence conserved.
    The intensity redistribution with respect to each single point
    is done by the weights of available pixels according
    to a gaussian distribution.
    All nans in arr, stay nans in gauss.
    """
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

if __name__ == "__main__":
    print("Blurring...")
    for day_data in glob.glob(f"{DAILY_IMAGE_DIR}/*.npy"):
        data = np.load(day_data)
        file_name = day_data.split("\\")[1]
        for i in range(data.shape[2]):
            if SHOULD_BLUR:
                data[:,:,i] = filter_nan_gaussian_conserving(data[:,:,i], SIGMA)

        np.save(FINAL_OUTPUT_DIR + "/" + file_name, data)
    print("Done.")

# plt.figure(figsize=(40,20))
# pos = plt.imshow(data[:,:,2], origin="lower")
# plt.colorbar(pos)
# plt.show()