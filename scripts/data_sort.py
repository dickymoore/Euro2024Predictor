import pandas as pd

def sortHomeData(team, data):
    winCount = 0
    data = data[data.home_team == team]
    for row in data.itertuples():
        if row.home_score > row.away_score:
            winCount += 1
    return winCount
            
def sortAwayData(team, data):
    # print(team)
    winCount = 0
    data = data[data.away_team == team]
    for row in data.itertuples():
        if row.home_score < row.away_score:
            # print(row.away_team + " wins")
            winCount += 1
    return winCount

startDate = pd.to_datetime('2021-03-05')
euroTeams = ['Albania', 'Austria', 'Belgium', 'Croatia', 'Czech Republic', 'Denmark', 'England', 'France', 'Georgia', 'Germany', 'Hungary', 'Italy', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Scotland', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Switzerland', 'Turkey', 'Ukraine']
data = pd.read_csv('data/raw/results.csv')
data['date'] = pd.to_datetime(data['date'])
data = data[data.date>startDate]
data = data[data.away_team.isin(euroTeams) | data.home_team.isin(euroTeams)]

def getWinPercentage(teams, data):
    data = data[data.away_team.isin(teams) | data.home_team.isin(teams)]
    for team in teams:
        numberOfGames = data[data.away_team.isin([team]) | data.home_team.isin([team])].shape[0]
        winCount = 0
        winCount += sortAwayData(team, data)
        winCount += sortHomeData(team, data)
        print(team, ' win %', round((winCount / numberOfGames) * 100, 2), ' of ', numberOfGames, ' games')
    
print(getWinPercentage(euroTeams, data))