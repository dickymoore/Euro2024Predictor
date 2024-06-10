import pandas as pd

def scrape_and_save_to_file():
    data_all = pd.read_csv('data/raw/results.csv') # read date in from csv
    home_teams = data_all["home_team"].unique().tolist()
    away_teams = data_all["away_team"].unique().tolist()
    all_teams = list(set(home_teams + away_teams))
    all_teams_cleaned = [x for x in all_teams if str(x) != 'nan']
    sorted_teams = sorted(all_teams_cleaned)
    with open('data/all_countries.csv', 'w') as f:
        for team in sorted_teams:
            f.write("%s\n" % team)
    
scrape_and_save_to_file()
