# Model cannot be uploaded to github all in one go so this
# file can split and unsplit the model

import os
import math
import glob

# Split the file into mulitple chunks.
# Only used 
def split(file_name):
    file = open(file_name, "rb")
    file_size = os.path.getsize(file_name)

    mb_size = file_size / 1_000_000
    print(mb_size)

    MB_SPLIT_SIZE = 50

    for i in range(0, math.ceil(mb_size / MB_SPLIT_SIZE), 1):
        print(i)
        bt = file.read(MB_SPLIT_SIZE * 1_000_000)
        print(len(bt))

        f = open(f"./res/model_chunks/model{i}.h5", "wb")
        f.write(bt)
        f.close()

    file.close()

# Combines all the files in a folder into one file
def unsplit(file_name):
    chunk_paths = glob.glob("./res/model_chunks/model*.h5")

    final_model = b""

    for chunk_path in chunk_paths:
        chunk_data_file = open(chunk_path, "rb")
        chunk_data = chunk_data_file.read()
        chunk_data_file.close()
        
        final_model += chunk_data

    f = open(file_name, "wb")
    f.write(final_model)
    f.close()

# split("model_32.h5")