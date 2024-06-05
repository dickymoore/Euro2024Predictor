import pandas as pd

startDate = pd.to_datetime('2021-03-05')

euroTeams = ['Albania', 'Austria', 'Belgium', 'Croatia', 'Czech Republic', 'Denmark', 'England', 'France', 'Georgia', 'Germany', 'Hungary', 'Italy', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Scotland', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Switzerland', 'Turkey', 'Ukraine']

data = pd.read_csv('source-data/results.csv')
data['date'] = pd.to_datetime(data['date'])
data = data[data.date>startDate]

data = data[data.away_team.isin(euroTeams) | data.home_team.isin(euroTeams)]

print(data)