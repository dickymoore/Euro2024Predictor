import pandas as pd

def compute_win_percentages(data, teams):
    win_percentage = {team: {'win_percentage': 0, 'no_games': 0} for team in teams}

    for team in teams:

        home_games = data[data['home_team'] == team.upper()]

        
        away_games = data[data['away_team'] == team.upper()]
        
        home_wins = (home_games['home_score'] > home_games['away_score']).sum()
        away_wins = (away_games['away_score'] > away_games['home_score']).sum()
        
        total_games = len(home_games) + len(away_games)
        total_wins = home_wins + away_wins

        win_percentage[team]['win_percentage'] = (total_wins / total_games * 100) if total_games > 0 else 0
        win_percentage[team]['no_games'] = total_games      

        data.loc[data['home_team'] == team.upper(), 'home_country_win_percentage'] = win_percentage.get(team)["win_percentage"]
        data.loc[data['away_team'] == team.upper(), 'away_country_win_percentage'] = win_percentage.get(team)["win_percentage"]
    
    return data
