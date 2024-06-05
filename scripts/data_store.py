import pandas as pd

def store_data(data, cache_path):
    data.to_pickle(cache_path)
