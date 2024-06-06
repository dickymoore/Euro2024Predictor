import pandas as pd

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

startDate = pd.to_datetime('2021-03-05')
dataAll = pd.read_csv('data/raw/results.csv')
dataAll['date'] = pd.to_datetime(dataAll['date'])
dataAll = dataAll[dataAll.date>startDate]
homeTeams = dataAll["home_team"].unique().tolist()
awayTeams = dataAll["away_team"].unique().tolist()
allTeams = list(set(homeTeams + awayTeams))
#data = data[data.away_team.isin(euroTeams) | data.home_team.isin(euroTeams)]

def getWinPercentage(teams, data):
    data = data[data.away_team.isin(teams) | data.home_team.isin(teams)]
    winPercentageAllCountries = pd.DataFrame(columns=('country',"win_percentage","no_games"))
    for team in teams:
        numberOfGames = data[data.away_team.isin([team]) | data.home_team.isin([team])].shape[0]
        winCount = 0
        winCount += sortAwayData(team, data)
        winCount += sortHomeData(team, data)
        if winCount != 0:
            new_row = {"country" : team, "win_percentage" : round((winCount / numberOfGames) * 100, 2), "no_games" : numberOfGames}
        else:
            new_row = {"country" : team, "win_percentage" : 0, "no_games" : numberOfGames}
        winPercentageAllCountries.loc[len(winPercentageAllCountries)] = new_row
    # print(winPercentageAllCountries)
    return winPercentageAllCountries
    

startDate = pd.to_datetime('2021-03-05')
euroTeams = ['Albania', 'Austria', 'Belgium', 'Croatia', 'Czech Republic', 'Denmark', 'England', 'France', 'Georgia', 'Germany', 'Hungary', 'Italy', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Scotland', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Switzerland', 'Turkey', 'Ukraine']
euroCountriesGames = pd.read_csv('data/raw/results.csv')
euroCountriesGames['date'] = pd.to_datetime(euroCountriesGames['date'])
euroCountriesGames = euroCountriesGames[euroCountriesGames.date>startDate]
euroCountriesGames = euroCountriesGames[euroCountriesGames.away_team.isin(euroTeams) | euroCountriesGames.home_team.isin(euroTeams)]



# winPercentageAllCountries = pd.read_pickle("filepath_or_buffer", compression='infer', storage_options=None)
# euroCountriesGames = pd.read_pickle("filepath_or_buffer", compression='infer', storage_options=None)

def weightedScoring(away_score, home_score, away_country, home_country, away_country_win_percentage, home_country_win_percentage):
    winner_country = "N/A"
    country_away = away_country
    country_home = home_country
    def scoring(winning_score, loosing_score, winning_country_win_percentage, loosing_country_win_percentage):
        number = (float(winning_score) * (100 - float(winning_country_win_percentage))) - (float(loosing_score) * (100 - float(loosing_country_win_percentage)))
        return number
    if away_score > home_score:
        winner_country = away_country
        away_country_weighted_score = scoring(away_score, home_score, away_country_win_percentage, home_country_win_percentage)
        home_country_weighted_score = scoring(home_score, away_score, home_country_win_percentage, away_country_win_percentage)
    elif home_score > away_score:
        winner_country = home_country
        away_country_weighted_score = scoring(away_score, home_score, away_country_win_percentage, home_country_win_percentage)
        home_country_weighted_score = scoring(home_score, away_score, home_country_win_percentage, away_country_win_percentage)
    else:
        away_country_weighted_score = ((1 + float(away_score)) * (100 - float(away_country_win_percentage))) - ((1 + float(home_score)) * (100 - float(home_country_win_percentage)))
        home_country_weighted_score = ((1 + float(home_score)) * (100 - float(home_country_win_percentage))) - ((1 + float(away_score)) * (100 - float(away_country_win_percentage)))
    return {"winner_country": winner_country, "country_away": country_away, "country_home": country_home, "away_country_weighted_score": away_country_weighted_score, "home_country_weighted_score": home_country_weighted_score}
    
    

def sortData():
    weightedScoringTable = pd.DataFrame(columns=("winner_country", "country_away", "country_home", "away_country_weighted_score", "home_country_weighted_score"))
    winPercentageTable = getWinPercentage(allTeams, dataAll)
    for row in euroCountriesGames.itertuples():
        new_row = weightedScoring(row.away_score, row.home_score, row.away_team, row.home_team, winPercentageTable.loc[winPercentageTable["country"] == row.away_team]["win_percentage"], winPercentageTable.loc[winPercentageTable["country"] == row.home_team]["win_percentage"])
        #getWinPercentage([row.away_team], dataAll)[row.away_team], getWinPercentage([row.home_team], dataAll)[row.home_team]
        weightedScoringTable.loc[len(weightedScoringTable)] = new_row
    weightedScoringTable.to_csv("filename.csv", sep=',', index=False, encoding='utf-8')
sortData()
