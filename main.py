from scripts.data_ingestion import load_data
from scripts.data_transform import transform_data
from scripts.data_store import store_data
from scripts.config import load_config

def main():
    config = load_config()
    teams = config['teams']
    look_back_days = config['look_back_days']
    
    csv_path = 'data/raw/data.csv'
    cache_path = 'data/cache/data.pkl'
    
    # Load data
    data = load_data(csv_path, cache_path)
    
    # Transform data
    data = transform_data(data, teams, look_back_days)
    
    # Store data
    store_data(data, cache_path)
    
    # Output data
    print(data.head())

if __name__ == "__main__":
    main()
