import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_file_modification_time(file_path):
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def read_cache_timestamp(cache_timestamp_path):
    if os.path.exists(cache_timestamp_path):
        if os.path.getsize(cache_timestamp_path) > 0:
            try:
                with open(cache_timestamp_path, 'r') as file:
                    cache_timestamp_string = file.read().strip()
                    cache_timestamp = datetime.strptime(cache_timestamp_string, "%Y-%m-%d %H:%M:%S")
                    logger.debug(f"Cache time: {cache_timestamp}")
                    return cache_timestamp
            except EOFError:
                logger.error(f"Error: {cache_timestamp_path} is empty or corrupted.")
                return None
            except Exception as e:
                logger.error(f"Error reading {cache_timestamp_path}: {e}")
                return None
        else:
            logger.warning(f"Error: {cache_timestamp_path} is empty.")
            return None
    return None

def store_data(data, cache_path, cache_timestamp_path):
    data.to_pickle(cache_path)
    with open(cache_timestamp_path, 'w') as file:
        current_time = datetime.now()
        file.write(current_time.strftime("%Y-%m-%d %H:%M:%S"))
