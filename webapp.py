from flask import Flask, render_template, request, jsonify
import pandas as pd
import subprocess
import os
from collections import defaultdict
import yaml

app = Flask(__name__)

def load_data(csv_path):
    return pd.read_csv(csv_path, na_values=[''])

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

    third_place_teams = standings_df.groupby('group').nth(2)
    third_place_teams = third_place_teams.sort_values(by=['points', 'gd', 'gf'], ascending=[False, False, False]).head(4)

    standings_df.loc[standings_df.groupby('group').head(2).index, 'qualified'] = 'qualified'
    standings_df.loc[third_place_teams.index, 'qualified'] = 'best-third'

    return standings_df

def organize_matches_by_group(data):
    match_results = defaultdict(list)
    knockout_matches = []

    for _, row in data.iterrows():
        team1_score = int(row['team1_score'])
        team2_score = int(row['team2_score'])
        team1_pen_score = int(row['team1_pso_score']) if pd.notna(row['team1_pso_score']) else None
        team2_pen_score = int(row['team2_pso_score']) if pd.notna(row['team2_pso_score']) else None

        match = {
            'team1': row['team1'],
            'team1_score': team1_score,
            'team2': row['team2'],
            'team2_score': team2_score,
            'team1_pen_score': team1_pen_score,
            'team2_pen_score': team2_pen_score,
            'stage': row['stage']
        }

        if row['stage'] == 'Group Stage':
            match_results[row['group']].append(match)
        else:
            if team1_score == team2_score and team1_pen_score is not None and team2_pen_score is not None:
                if team1_pen_score > team2_pen_score:
                    match['team1_class'] = 'winner'
                    match['team2_class'] = 'loser'
                else:
                    match['team1_class'] = 'loser'
                    match['team2_class'] = 'winner'
            else:
                match['team1_class'] = 'winner' if team1_score > team2_score else 'loser'
                match['team2_class'] = 'winner' if team2_score > team1_score else 'loser'

            knockout_matches.append(match)

    return match_results, knockout_matches

@app.route("/")
def index():
    csv_path = "data/results/all_stage_results.csv"
    data = load_data(csv_path)

    standings = compute_standings(data)
    match_results, knockout_matches = organize_matches_by_group(data)

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.yaml')

    # Load the configuration values
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    weighted_win_percentage_weight = config.get('weighted_win_percentage_weight', 1)
    home_advantage = config.get('home_advantage', 0.1)
    look_back_months = config.get('look_back_months', 36)

    return render_template(
        "index.html",
        standings=standings,
        match_results=match_results,
        knockout_matches=knockout_matches,
        weighted_win_percentage_weight=weighted_win_percentage_weight,
        home_advantage=home_advantage,
        look_back_months=look_back_months
    )

@app.route("/run_predictor", methods=["POST"])
def run_predictor():
    try:
        data = request.get_json()
        weighted_win_percentage_weight = data.get('weighted_win_percentage_weight', 1)
        home_advantage = data.get('home_advantage', 0.1)
        look_back_months = data.get('look_back_months', 36)

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.yaml')

        # Update the config.yaml file with the new values
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        config['weighted_win_percentage_weight'] = float(weighted_win_percentage_weight)
        config['home_advantage'] = float(home_advantage)
        config['look_back_months'] = int(look_back_months)

        with open(config_path, 'w') as file:
            yaml.safe_dump(config, file)

        python_interpreter = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')
        subprocess.run([python_interpreter, "main.py"], check=True)

        return jsonify({"status": "success"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
