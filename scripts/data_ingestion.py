import os
import pandas as pd

def load_data(csv_path, cache_path):
    if os.path.exists(cache_path):
        print("Loading data from cache...")
        return pd.read_pickle(cache_path)
    else:
        print("Loading data from CSV...")
        data = pd.read_csv(csv_path)
        data.to_pickle(cache_path)
        return data
