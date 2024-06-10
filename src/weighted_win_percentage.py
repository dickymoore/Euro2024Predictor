import pandas as pd
import csv

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
    
    return winPercentageAllCountries


# old magic
# example home wins 3 - 1

# home weighted score: 
# (3 * (100 - 75) - (1  * ( 100 - 50)) = 75  
#
# away weighted score:
# (1 * ((100 - 50)) - (3 * (100 - 75)) = -75
#
# always +- the same score

# new magic
# modifier should factor in circumstances (quality of opp, goal diff, etc)
# for now ...
# winning: 0.5 + 0.5(winners win percentage) => 0.5 + (0.2) = 0.70 
# losing: 0 + 0.5(winners win percentage) => 0 + 0.5*0.6 = 0.30
# draw: 0.5 (for now - prob should be weight on opp strength too)
# 

def weightedScoring(country_ranking, away_score, home_score, away_country, home_country, away_country_win_percentage, home_country_win_percentage):
    
    winner_country = "N/A"

    if(away_country not in country_ranking):
        country_ranking[away_country] = 0.5
    if(home_country not in country_ranking):
        country_ranking[home_country] = 0.5
        
    
    if away_score > home_score:
        winner_country = away_country

        away_country_weighted_score = (0.5 + (0.25*(float(home_country_win_percentage.iloc[0])/100)) + 0.25*country_ranking.get(home_country))
        home_country_weighted_score = (0.5*(float(away_country_win_percentage.iloc[0])/100) + 0.5*country_ranking.get(away_country))

        country_ranking[home_country] = home_country_weighted_score
        country_ranking[away_country] = away_country_weighted_score   
        
    elif home_score > away_score:
        winner_country = home_country
        home_country_weighted_score = (0.5 + 0.25*(float(away_country_win_percentage.iloc[0])/100) + 0.25*country_ranking.get(away_country))
        away_country_weighted_score = (0.5*float(home_country_win_percentage.iloc[0])/100 + 0.5*country_ranking.get(home_country))


        country_ranking[home_country] = home_country_weighted_score
        country_ranking[away_country] = away_country_weighted_score    
    
   
    else:
        home_country_weighted_score = ((0.95*country_ranking.get(home_country)) + (0.05*country_ranking.get(away_country)))
        away_country_weighted_score = ((0.95*country_ranking.get(away_country)) + (0.05*country_ranking.get(home_country)))
        
        country_ranking[home_country] = home_country_weighted_score
        country_ranking[away_country] = away_country_weighted_score    


     
    return {
        "winner_country": winner_country, 
        "country_home": home_country, 
        "home_country_weighted_score": home_country_weighted_score,
        "country_away": away_country, 
        "away_country_weighted_score": away_country_weighted_score,
        "home rank": country_ranking[home_country],
        "away rank": country_ranking[away_country]}        

def sort_data(all_teams, data_all, euroCountriesGames):

    weightedScoringTable = pd.DataFrame(columns=("winner_country", "country_home","home_country_weighted_score", "country_away", "away_country_weighted_score","home rank", "away rank"))
    winPercentageTable = getWinPercentage(all_teams, data_all)

    country_ranking = {}


    for row in euroCountriesGames.itertuples():
        new_row = weightedScoring(
            country_ranking,
            row.away_score, 
            row.home_score, 
            row.away_team, 
            row.home_team, 
            winPercentageTable.loc[winPercentageTable["country"] == row.away_team]["win_percentage"], 
            winPercentageTable.loc[winPercentageTable["country"] == row.home_team]["win_percentage"])


        weightedScoringTable.loc[len(weightedScoringTable)] = new_row

    print(country_ranking)
    

    with open("mycsvfile.csv", "w", newline="") as f:
        w = csv.DictWriter(f, country_ranking.keys())
        w.writeheader()
        w.writerow(country_ranking)

    weightedScoringTable.to_csv("filename.csv", sep=',', index=False, encoding='utf-8')


