import os
import pickle
from datetime import datetime

from scripts.data_ingestion import load_data
from scripts.data_transform import transform_data
from scripts.data_store import store_data
from scripts.config import load_config

def get_file_modification_time(file_path):
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def read_cache_timestamp(cache_timestamp_path):
    if os.path.exists(cache_timestamp_path):
        with open(cache_timestamp_path, 'rb') as file:
            return pickle.load(file)
    return None

def write_cache_timestamp(cache_timestamp_path, timestamp):
    with open(cache_timestamp_path, 'wb') as file:
        pickle.dump(timestamp, file)

def main():
    print("Loading configuration...")
    config = load_config()
    teams = config['teams']
    look_back_months = config['look_back_months']
    print(f"""Configuration is: 
teams={teams} 
look_back_months={look_back_months}""")

    # csv_path = 'data/raw/data.csv'
    # cache_path = 'data/cache/data.pkl'
    # cache_timestamp_path = 'data/cache/data_timestamp.pkl'

    # print("Checking data freshness...")
    # raw_data_mod_time = get_file_modification_time(csv_path)
    # cache_data_mod_time = read_cache_timestamp(cache_timestamp_path)

    # if cache_data_mod_time and raw_data_mod_time <= cache_data_mod_time:
    #     print("Loading data from cache...")
    #     data = load_data(cache_path)
    #     print("Data loaded from cache.")
    # else:
    #     print("Loading data from raw source...")
    #     data = load_data(csv_path, cache_path=None)
    #     print("Data loaded from raw source.")

    #     print("Transforming data...")
    #     data = transform_data(data, teams, look_back_months)
    #     print("Data transformed successfully.")

    #     print("Storing data to cache...")
    #     store_data(data, cache_path)
    #     write_cache_timestamp(cache_timestamp_path, raw_data_mod_time)
    #     print("Data stored to cache.")

    # print("Outputting data preview...")
    # print(data.head())

if __name__ == "__main__":
    main()
