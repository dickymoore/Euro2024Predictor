import pandas as pd
from scripts.config import load_config

def sortHomeData(team, data):
    winCount = 0
    data = data[data.home_team == team]
    for row in data.itertuples():
        if row.home_score > row.away_score:
            winCount += 1
    return winCount

def sortAwayData(team, data):
    winCount = 0
    data = data[data.away_team == team]
    for row in data.itertuples():
        if row.home_score < row.away_score:
            winCount += 1
    return winCount

def getWinPercentage(teams, data):
    data = data[data.away_team.isin(teams) | data.home_team.isin(teams)]
    winPercentageEuroCountries = pd.DataFrame(columns=('country', "win_percentage", "no_games"))
    for team in teams:
        numberOfGames = data[data.away_team.isin([team]) | data.home_team.isin([team])].shape[0]
        winCount = 0
        winCount += sortAwayData(team, data)
        winCount += sortHomeData(team, data)
        new_row = {"country": team, "win_percentage": round((winCount / numberOfGames) * 100, 2), "no_games": numberOfGames}
        winPercentageEuroCountries.loc[len(winPercentageEuroCountries)] = new_row
    print(winPercentageEuroCountries)

if __name__ == "__main__":
    config = load_config()
    teams = [team for group in config['teams'].values() for team in group]
    startDate = pd.to_datetime('2021-03-05')
    data = pd.read_csv('data/raw/results.csv')
    data['date'] = pd.to_datetime(data['date'])
    data = data[data.date > startDate]
    data = data[data.away_team.isin(teams) | data.home_team.isin(teams)]

    getWinPercentage(teams, data)
