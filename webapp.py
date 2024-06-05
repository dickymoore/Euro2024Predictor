from flask import Flask, render_template
import pandas as pd
from collections import defaultdict

app = Flask(__name__)

def load_data(csv_path):
    return pd.read_csv(csv_path)

def compute_standings(data):
    standings = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for _, row in data.iterrows():
        if row['stage'] != 'Group Stage':
            continue

        group = row['group']
        team1 = row['team1']
        team2 = row['team2']
        team1_score = int(row['team1_score'])
        team2_score = int(row['team2_score'])

        if team1_score > team2_score:
            standings[group][team1]['points'] += 3
            standings[group][team1]['w'] += 1
            standings[group][team2]['l'] += 1
        elif team1_score < team2_score:
            standings[group][team2]['points'] += 3
            standings[group][team2]['w'] += 1
            standings[group][team1]['l'] += 1
        else:
            standings[group][team1]['points'] += 1
            standings[group][team2]['points'] += 1
            standings[group][team1]['d'] += 1
            standings[group][team2]['d'] += 1

        standings[group][team1]['gf'] += team1_score
        standings[group][team1]['ga'] += team2_score
        standings[group][team1]['gd'] += team1_score - team2_score
        standings[group][team1]['gp'] += 1

        standings[group][team2]['gf'] += team2_score
        standings[group][team2]['ga'] += team1_score
        standings[group][team2]['gd'] += team2_score - team1_score
        standings[group][team2]['gp'] += 1

    standings_df = []
    for group, teams in standings.items():
        for team, stats in teams.items():
            standings_df.append({
                'group': group,
                'team': team,
                'points': stats['points'],
                'gp': stats['gp'],
                'w': stats['w'],
                'd': stats['d'],
                'l': stats['l'],
                'gf': stats['gf'],
                'ga': stats['ga'],
                'gd': stats['gd'],
                'qualified': 'unqualified'
            })

    standings_df = pd.DataFrame(standings_df)
    standings_df = standings_df.sort_values(by=['group', 'points', 'gd', 'gf'], ascending=[True, False, False, False])

    # Identify the best third-placed teams
    third_place_teams = standings_df.groupby('group').nth(2)
    third_place_teams = third_place_teams.sort_values(by=['points', 'gd', 'gf'], ascending=[False, False, False]).head(4)

    standings_df.loc[standings_df.groupby('group').head(2).index, 'qualified'] = 'qualified'
    standings_df.loc[third_place_teams.index, 'qualified'] = 'best-third'

    return standings_df

def parse_score(score):
    score_str = str(score)
    if "pen" in score_str:
        score_str = score_str.split()[0]
    return int(score_str)


def organize_matches_by_group(data):
    match_results = defaultdict(list)
    knockout_matches = []

    for _, row in data.iterrows():
        team1_score = parse_score(row['team1_score'])
        team2_score = parse_score(row['team2_score'])
        
        match = {
            'team1': row['team1'],
            'team1_score': team1_score,
            'team2': row['team2'],
            'team2_score': team2_score
        }

        if row['stage'] == 'Group Stage':
            match_results[row['group']].append(match)
        else:
            match['stage'] = row['stage']
            knockout_matches.append(match)

    return match_results, knockout_matches

@app.route("/")
def index():
    csv_path = "data/dummy-results.csv"
    data = load_data(csv_path)

    standings = compute_standings(data)
    match_results, knockout_matches = organize_matches_by_group(data)
    
    return render_template("index.html", standings=standings, match_results=match_results, knockout_matches=knockout_matches)

if __name__ == "__main__":
    app.run(debug=True)
