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

        # ranking: if you win -> 0.25 + 0.25*your ranking + 
        away_country_weighted_score =  (1.1*country_ranking.get(away_country)) + 0.1*country_ranking.get(home_country)
        home_country_weighted_score = (0.95*country_ranking.get(home_country)) - 0.05*country_ranking.get(away_country)

        country_ranking[home_country] = home_country_weighted_score
        country_ranking[away_country] = away_country_weighted_score 
        
    elif home_score > away_score:
        winner_country = home_country
        away_country_weighted_score =  (0.95*country_ranking.get(away_country)) - 0.05*country_ranking.get(home_country)
        home_country_weighted_score = (1.1*country_ranking.get(home_country)) + 0.1*country_ranking.get(away_country)

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

def sort_data(all_teams, euro_teams, data_all, euroCountriesGames):

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

    
    country_ranking = dict(sorted(country_ranking.items(), key=lambda item: item[1]))
    

    for country in tuple(country_ranking.keys()): 
        if country not in euro_teams:
            country_ranking.pop(country)
    
    

    with open("mycsvfile.csv", "w", newline="") as f:
        w = csv.DictWriter(f, country_ranking.keys())
        w.writeheader()
        w.writerow(country_ranking)

    weightedScoringTable.to_csv("filename.csv", sep=',', index=False, encoding='utf-8')
    
    return country_ranking


def read_teams_from_file():
    with open('data/raw/all_countries.csv', newline='') as f:
        reader = csv.reader(f)
        all_teams = []
        for team in list(reader):
            all_teams.append(str(team[0]))
        

    with open('data/raw/euros_countries.csv', newline='') as f:
        reader = csv.reader(f)
        euro_teams = []
        for team in list(reader):
            euro_teams.append(str(team[0]))
    
    return all_teams, euro_teams

start_date = pd.to_datetime('2021-03-05')

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


def output ():
    all_teams, euro_teams = read_teams_from_file()
    start_date = pd.to_datetime('2021-03-05') # define start date 
    data_all = get_all_matches_in_date_range(start_date)
    euro_countries_games = get_euroteam_matches_in_date_range(start_date, euro_teams)
    return sort_data(all_teams, euro_teams, data_all, euro_countries_games)
