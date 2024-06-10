import csv 
def read_teams_from_file():
    with open('data/all_countries.csv', newline='') as f:
        reader = csv.reader(f)
        all_teams = []
        for team in list(reader):
            all_teams.append(str(team[0]))
        

    with open('data/euros_countries.csv', newline='') as f:
        reader = csv.reader(f)
        euro_teams = []
        for team in list(reader):
            euro_teams.append(str(team[0]))
    
    return all_teams, euro_teams