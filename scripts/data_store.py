import pandas as pd
import pickle
from datetime import datetime

def store_data(data, cache_path,cache_timestamp_path):
    data.to_pickle(cache_path)
    with open(cache_timestamp_path, 'w') as file:
        current_time = datetime.now()  # Define current_time here
        file.write(current_time.strftime("%Y-%m-%d %H:%M:%S"))  # Store the current time in a specific string format
