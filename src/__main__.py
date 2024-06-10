import pandas as pd 
from weighted_win_percentage import sort_data
from filter_data_by_date import get_all_matches_in_date_range
from filter_data_by_date import get_euroteam_matches_in_date_range
from read_teams_from_file import read_teams_from_file

def main():
    all_teams, euro_teams = read_teams_from_file()
    start_date = pd.to_datetime('2021-03-05') # define start date 
    data_all = get_all_matches_in_date_range(start_date)
    euro_countries_games = get_euroteam_matches_in_date_range(start_date, euro_teams)
    sort_data(all_teams, data_all, euro_countries_games)

if __name__ == "__main__":
    main()