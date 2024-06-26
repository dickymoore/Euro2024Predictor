import pandas as pd

def calculate_weighted_win_percentage(df):
    # Ensure correct data types
    df['away_score'] = df['away_score'].astype(float)
    df['home_score'] = df['home_score'].astype(float)
    df['away_country_win_percentage'] = df['away_country_win_percentage'].astype(float)
    df['home_country_win_percentage'] = df['home_country_win_percentage'].astype(float)

    # Calculate weighted scores
    df['away_country_weighted_score'] = (df['away_score'] * (df['away_country_win_percentage'] / 100)) - (df['home_score'] * (df['home_country_win_percentage'] / 100))
    df['home_country_weighted_score'] = (df['home_score'] * (df['home_country_win_percentage'] / 100)) - (df['away_score'] * (df['away_country_win_percentage'] / 100))

    return df

def weightedScoring(away_score, home_score, away_country, home_country, away_country_win_percentage, home_country_win_percentage):
    winner_country = "N/A"
    country_away = away_country
    country_home = home_country
    def scoring(winning_score, loosing_score, winning_country_win_percentage, loosing_country_win_percentage):
        if winning_score == loosing_score:
            winning_number = (float(winning_score) * (float(loosing_country_win_percentage)/100))
            loosing_number = (float(loosing_score) * (float(winning_country_win_percentage)/100))
        else:
            winning_number = (float(winning_score) * (float(loosing_country_win_percentage)/100)) + (float(loosing_score) * (float(winning_country_win_percentage)/100))
            loosing_number = (float(winning_score) * (float(loosing_country_win_percentage)/100)) - (float(loosing_score) * (float(winning_country_win_percentage)/100))
        return [winning_number, loosing_number]
    winning_country_weighted_score = scoring(away_score, home_score, away_country_win_percentage, home_country_win_percentage)[0]
    loosing_country_weighted_score = scoring(away_score, home_score, away_country_win_percentage, home_country_win_percentage)[1]
    if away_score > home_score:
        winner_country = away_country
        away_country_weighted_score = winning_country_weighted_score
        home_country_weighted_score = loosing_country_weighted_score
    else:
        winner_country = home_country
        home_country_weighted_score = winning_country_weighted_score
        away_country_weighted_score = loosing_country_weighted_score
    return {"winner_country": winner_country, "country_away": country_away, "country_home": country_home, "away_score": away_score, "home_score": home_score, "away_country_win_percentage": away_country_win_percentage, "home_country_win_percentage": home_country_win_percentage,  "away_country_weighted_score": away_country_weighted_score, "home_country_weighted_score": home_country_weighted_score}

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
    winPercentageAllCountries = pd.DataFrame(columns=('country', "win_percentage", "no_games"))
    for team in teams:
        numberOfGames = data[data.away_team.isin([team]) | data.home_team.isin([team])].shape[0]
        winCount = 0
        winCount += sortAwayData(team, data)
        winCount += sortHomeData(team, data)
        if winCount != 0:
            new_row = {"country": team, "win_percentage": round((winCount / numberOfGames) * 100, 2), "no_games": numberOfGames}
        else:
            new_row = {"country": team, "win_percentage": 0, "no_games": numberOfGames}
        winPercentageAllCountries.loc[len(winPercentageAllCountries)] = new_row
    winPercentageAllCountries.to_csv("winPercentage.csv", sep=',', index=False, encoding='utf-8')
    return winPercentageAllCountries

def sortData(euroCountriesGames, winPercentageTable):
    weightedScoringTable = pd.DataFrame(columns=("winner_country", "country_away", "country_home", "away_score", "home_score", "away_country_win_percentage", "home_country_win_percentage", "away_country_weighted_score", "home_country_weighted_score"))
    for row in euroCountriesGames.itertuples():
        new_row = weightedScoring(row.away_score, row.home_score, row.away_team, row.home_team, 
                                  float(winPercentageTable.loc[winPercentageTable["country"] == row.away_team, "win_percentage"]),
                                  float(winPercentageTable.loc[winPercentageTable["country"] == row.home_team, "win_percentage"]))
        weightedScoringTable.loc[len(weightedScoringTable)] = new_row
    return weightedScoringTable

def sortHomeScore(team, data):
    totalWeightedScore = 0
    data = data[data.country_home == team]
    for row in data.itertuples():
        totalWeightedScore += float(row.home_country_weighted_score)
    return totalWeightedScore

def sortAwayScore(team, data):
    totalWeightedScore = 0
    data = data[data.country_away == team]
    for row in data.itertuples():
        totalWeightedScore += float(row.away_country_weighted_score)
    return totalWeightedScore

def getWeightedScores(euroCountriesGames, allTeams, dataAll):
    winPercentageTable = getWinPercentage(allTeams, dataAll)
    allGamesWeightedScoringTable = sortData(euroCountriesGames, winPercentageTable).dropna()
    weightedScoresAllCountries = pd.DataFrame(columns=("country", "weighted_score", "no.games"))
    for team in allTeams:
        numberOfGames = allGamesWeightedScoringTable[allGamesWeightedScoringTable.country_away.isin([team]) | allGamesWeightedScoringTable.country_home.isin([team])].shape[0]
        totalWeightedScore = 0
        totalWeightedScore += sortHomeScore(team, allGamesWeightedScoringTable)
        totalWeightedScore += sortAwayScore(team, allGamesWeightedScoringTable)
        if totalWeightedScore == 0:
            new_row = {"country": team, "weighted_score": 0, "no.games": numberOfGames}
        else:    
            new_row = {"country": team, "weighted_score": totalWeightedScore / numberOfGames, "no.games": numberOfGames}
        weightedScoresAllCountries.loc[len(weightedScoresAllCountries)] = new_row
    weightedScoresAllCountries.to_csv("weightedScoring.csv", sep=',', index=False, encoding='utf-8')
    return weightedScoresAllCountries

def main():
    startDate = pd.to_datetime('2021-03-05')
    dataAll = pd.read_csv('data/raw/results.csv')
    dataAll['date'] = pd.to_datetime(dataAll['date'])
    dataAll = dataAll[dataAll.date > startDate]
    
    homeTeams = dataAll["home_team"].unique().tolist()
    awayTeams = dataAll["away_team"].unique().tolist()
    allTeams = list(set(homeTeams + awayTeams))
    
    euroTeams = ['Albania', 'Austria', 'Belgium', 'Croatia', 'Czechia', 'Denmark', 'England', 'France', 'Georgia', 'Germany', 'Hungary', 'Italy', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Scotland', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Switzerland', 'Turkey', 'Ukraine']
    euroCountriesGames = pd.read_csv('data/raw/results.csv')
    euroCountriesGames['date'] = pd.to_datetime(euroCountriesGames['date'])
    euroCountriesGames = euroCountriesGames[euroCountriesGames.date > startDate]
    euroCountriesGames = euroCountriesGames[euroCountriesGames.away_team.isin(euroTeams) | euroCountriesGames.home_team.isin(euroTeams)]

    weightedScoresAllCountries = getWeightedScores(euroCountriesGames, allTeams, dataAll)
    print(weightedScoresAllCountries)

if __name__ == "__main__":
    main()
