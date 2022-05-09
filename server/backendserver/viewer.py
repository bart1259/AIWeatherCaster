import matplotlib.pyplot as plt
import numpy as np

d = np.load("../../data_collecter/final_output/1990-06-02_img.npy")
print(d.shape)

plt.figure(figsize=(20, 10), dpi=80)
plt.imshow(d[:,:,2], origin="lower")
plt.colorbar()
plt.show()