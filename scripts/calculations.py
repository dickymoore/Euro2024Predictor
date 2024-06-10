import pandas as pd
import logging

from scripts.data_transform import transform_data
from scripts.win_percentages import compute_win_percentages
from scripts.weighted_win_percentage import calculate_weighted_win_percentage
from scripts.cache import get_file_modification_time, read_cache_timestamp, store_data

logger = logging.getLogger(__name__)

def perform_calculations(config):
    teams = [team for group in config['teams'].values() for team in group]
    look_back_months = config['look_back_months']
    
    input_path = 'data/raw/results.csv'
    cache_path = 'data/cache/data.pkl'
    cache_timestamp_path = 'data/cache/data_timestamp.txt'

    raw_data_mod_time = get_file_modification_time(input_path)
    cache_data_mod_time = read_cache_timestamp(cache_timestamp_path)
    logger.debug("Checking data freshness...")
    logger.debug(f"Raw results data last updated: {raw_data_mod_time}")
    logger.debug(f"Cached results data updated: {cache_data_mod_time}")
    
    if cache_data_mod_time is None or raw_data_mod_time > cache_data_mod_time:
        logger.debug(f"Loading data from {input_path}")
        raw_data = pd.read_csv(input_path)
        num_raw_rows = raw_data.shape[0]
        logger.debug(f'{num_raw_rows} lines of raw_data have been loaded from {input_path}.')
        transformed_data = transform_data(raw_data, teams, look_back_months)
        transformed_data = compute_win_percentages(transformed_data, teams)
        num_transformed_rows = transformed_data.shape[0]
        logger.debug(f'{num_transformed_rows} lines of transformed data.')
        assert num_transformed_rows < num_raw_rows, f"Error: Transformed data ({num_transformed_rows} lines) is not less than raw data ({num_raw_rows} lines)."
        store_data(transformed_data, cache_path, cache_timestamp_path)
    else:
        logger.debug("Loading data from cache...")
        transformed_data = pd.read_pickle(cache_path)
        num_cached_rows = transformed_data.shape[0]
        logger.debug(f'{num_cached_rows} lines of raw_data have been loaded from cache.')

    transformed_data = compute_win_percentages(transformed_data, teams)
    logger.debug(f"Columns in transformed_data: {transformed_data.columns.tolist()}")
    
    weighted_win_data = calculate_weighted_win_percentage(transformed_data)
    weighted_win_data.to_csv('data/tmp/weighted_win_percentage_wide.csv', index=False)
    logger.info("Weighted win percentage data saved to data/tmp/weighted_win_percentage_wide.csv")

    # Generate the additional CSV for Euro 2024 teams, ordered by win percentage
    win_percentage_summary = pd.DataFrame(columns=['team', 'win_percentage'])
    
    # Combine home and away win percentages into a single DataFrame
    home_win_percentages = transformed_data[['home_team', 'home_country_win_percentage']].rename(
        columns={'home_team': 'team', 'home_country_win_percentage': 'win_percentage'}
    )
    away_win_percentages = transformed_data[['away_team', 'away_country_win_percentage']].rename(
        columns={'away_team': 'team', 'away_country_win_percentage': 'win_percentage'}
    )
    
    win_percentage_summary = pd.concat([home_win_percentages, away_win_percentages])
    
    # Group by team and calculate the mean win percentage
    win_percentage_summary = win_percentage_summary.groupby('team').mean().reset_index()
    
    # Filter for Euro 2024 teams only
    win_percentage_summary = win_percentage_summary[win_percentage_summary['team'].isin(teams)]
    
    # Sort by win percentage in descending order
    win_percentage_summary = win_percentage_summary.sort_values(by='win_percentage', ascending=False)
    
    # Save to CSV
    win_percentage_summary.to_csv('data/tmp/euro_teams_win_percentage.csv', index=False)
    logger.info("Euro teams win percentage data saved to data/tmp/euro_teams_win_percentage.csv")