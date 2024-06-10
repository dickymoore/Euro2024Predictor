import pandas as pd

def get_all_matches_in_date_range(start_date):
    data_all = pd.read_csv('data/raw/results.csv') # read date in from csv
    data_all['date'] = pd.to_datetime(data_all['date']) # convert date column to a datetime dtype
    data_all = data_all[data_all.date>start_date] # remove data from before start date 
    return data_all

def get_euroteam_matches_in_date_range(start_date, euro_teams):
    euro_countries_games = pd.read_csv('data/raw/results.csv')
    euro_countries_games['date'] = pd.to_datetime(euro_countries_games['date'])
    euro_countries_games = euro_countries_games[euro_countries_games.date>start_date]
    euro_countries_games = euro_countries_games[euro_countries_games.away_team.isin(euro_teams) | euro_countries_games.home_team.isin(euro_teams)]
    return euro_countries_games

