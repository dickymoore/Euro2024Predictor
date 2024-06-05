import os
import pandas as pd
import pickle
from datetime import datetime

from scripts.data_transform import transform_data
from scripts.data_store import store_data
from scripts.config import load_config

def get_file_modification_time(file_path):
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def read_cache_timestamp(cache_timestamp_path):
    if os.path.exists(cache_timestamp_path):
        if os.path.getsize(cache_timestamp_path) > 0:
            try:
                with open(cache_timestamp_path, 'r') as file:
                    cache_timestamp_string = file.read().strip()
                    cache_timestamp = datetime.strptime(cache_timestamp_string, "%Y-%m-%d %H:%M:%S")
                    print(f"Cache time: {cache_timestamp}")
                    return cache_timestamp
            except EOFError:
                print(f"Error: {cache_timestamp_path} is empty or corrupted.")
                return None
            except Exception as e:
                print(f"Error reading {cache_timestamp_path}: {e}")
                return None
        else:
            print(f"Error: {cache_timestamp_path} is empty.")
            return None
    return None

def main():
    config = load_config()
    teams = config['teams']
    look_back_months = config['look_back_months']
    print(f"""
Configuration is: 
teams={teams} 
look_back_months={look_back_months}
""")

    csv_path = 'data/raw/results.csv'
    cache_path = 'data/cache/data.pkl'
    cache_timestamp_path = 'data/cache/data_timestamp.pkl'

    raw_data_mod_time = get_file_modification_time(csv_path)
    cache_data_mod_time = read_cache_timestamp(cache_timestamp_path)
    print("Checking data freshness...")
    print(f"Raw results data last updated: {raw_data_mod_time}")
    print(f"Cached results data updated: {cache_data_mod_time}")
    
    if cache_data_mod_time is None or raw_data_mod_time > cache_data_mod_time:
        print(f"Loading data from {csv_path}")
        raw_data = pd.read_csv(csv_path)
        num_raw_rows = raw_data.shape[0]
        print(f'{num_raw_rows} lines of raw_data have been loaded from {csv_path}.')
        transformed_data = transform_data(raw_data, teams, look_back_months)
        num_transformed_rows = transformed_data.shape[0]
        print(f'{num_transformed_rows} lines of transformed data.')
        assert num_transformed_rows < num_raw_rows, f"Error: Transformed data ({num_transformed_rows} lines) is not less than raw data ({num_raw_rows} lines)."
        store_data(transformed_data, cache_path,cache_timestamp_path)
    else:
        print("Loading data from cache...")
        data = pd.read_pickle(cache_path)
        num_cached_rows = data.shape[0]
        print(f'{num_cached_rows} lines of raw_data have been loaded from cache.')


if __name__ == "__main__":
    main()
