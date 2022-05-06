import matplotlib.pyplot as plt
import numpy as np

d = np.load("./data/truth/2022-05-01.npy")
print(d.shape)

plt.figure(figsize=(20, 10), dpi=80)
plt.imshow(d[:,:,7], origin="lower")
plt.colorbar()
plt.show()