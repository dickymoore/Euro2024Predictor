from flask import Flask, render_template, request, jsonify
import pandas as pd
import subprocess
import os
import logging
from collections import defaultdict
import yaml
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_data(csv_path):
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        raise FileNotFoundError(f"File {csv_path} not found within the timeout period.")
    else:
        logger.debug(f"Reading CSV: {csv_path}")
        data = pd.read_csv(csv_path, na_values=[''])
        logger.debug(f"Data columns: {data.columns.tolist()}")
        return data

def compute_standings(data):
    logger.debug("Computing standings")
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

    logger.debug(f"Standings computed: {standings_df}")
    return standings_df

def organize_matches_by_group(data):
    logger.debug("Organizing matches by group")
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

    logger.debug(f"Match results organized: {match_results}")
    return match_results, knockout_matches

def wait_for_calculations(log_path, timeout=300, poll_interval=100):
    """
    Waits for the calculations to complete by monitoring the log file.

    :param log_path: Path to the log file.
    :param timeout: Maximum time to wait in seconds.
    :param poll_interval: Time interval between polling in milliseconds.
    :return: None
    """
    start_time = time.time()
    poll_interval_seconds = poll_interval / 1000.0  # Convert milliseconds to seconds
    while time.time() - start_time < timeout:
        with open(log_path, 'r') as log_file:
            logs = log_file.read()
            if 'Calculations complete' in logs:
                return
        time.sleep(poll_interval_seconds)
    raise TimeoutError("Timed out waiting for calculations to complete.")

@app.route("/")
def index():
    # Set default values with structure
    match_results = {
        'A': [
            {'team1': 'Team 1A', 'team1_score': 0, 'team2': 'Team 2A', 'team2_score': 0},
            {'team1': 'Team 3A', 'team1_score': 0, 'team2': 'Team 4A', 'team2_score': 0}
        ],
        'B': [
            {'team1': 'Team 1B', 'team1_score': 0, 'team2': 'Team 2B', 'team2_score': 0},
            {'team1': 'Team 3B', 'team1_score': 0, 'team2': 'Team 4B', 'team2_score': 0}
        ]
    }

    standings = pd.DataFrame({
        'group': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
        'team': ['Team 1A', 'Team 2A', 'Team 3A', 'Team 4A', 'Team 1B', 'Team 2B', 'Team 3B', 'Team 4B'],
        'gp': [0, 0, 0, 0, 0, 0, 0, 0],
        'w': [0, 0, 0, 0, 0, 0, 0, 0],
        'd': [0, 0, 0, 0, 0, 0, 0, 0],
        'l': [0, 0, 0, 0, 0, 0, 0, 0],
        'gf': [0, 0, 0, 0, 0, 0, 0, 0],
        'ga': [0, 0, 0, 0, 0, 0, 0, 0],
        'gd': [0, 0, 0, 0, 0, 0, 0, 0],
        'points': [0, 0, 0, 0, 0, 0, 0, 0],
        'qualified': ['', '', '', '', '', '', '', '']
    })

    knockout_matches = [
        {'stage': 'Round of 16', 'team1': 'Team 1A', 'team1_score': 0, 'team2': 'Team 2B', 'team2_score': 0, 'team1_pen_score': None, 'team2_pen_score': None, 'team1_class': '', 'team2_class': ''},
        {'stage': 'Quarter-final', 'team1': 'Team 1C', 'team1_score': 0, 'team2': 'Team 2D', 'team2_score': 0, 'team1_pen_score': None, 'team2_pen_score': None, 'team1_class': '', 'team2_class': ''},
        {'stage': 'Semi-final', 'team1': 'Team 1E', 'team1_score': 0, 'team2': 'Team 2F', 'team2_score': 0, 'team1_pen_score': None, 'team2_pen_score': None, 'team1_class': '', 'team2_class': ''},
        {'stage': 'Final', 'team1': 'Team 1G', 'team1_score': 0, 'team2': 'Team 2H', 'team2_score': 0, 'team1_pen_score': None, 'team2_pen_score': None, 'team1_class': '', 'team2_class': ''}
    ]

    logger.debug("Rendering index page with default values")
    return render_template(
        "index.html", 
        match_results=match_results, 
        standings=standings, 
        knockout_matches=knockout_matches
    )

@app.route("/run_predictor", methods=["POST"])
def run_predictor():
    logger.debug("Running predictor")
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

        # Trigger main.py to run in a separate process
        python_interpreter = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')
        subprocess.Popen([python_interpreter, "main.py"])

        # Wait for calculations to complete
        wait_for_calculations('data/tmp/predictor.log', poll_interval=100)  # Polling interval in milliseconds

        return jsonify({"status": "success"})
    except TimeoutError as te:
        logger.error(f"Timeout in run_predictor: {te}")
        return jsonify({"status": "error", "message": str(te)})
    except Exception as e:
        logger.error(f"Error in run_predictor: {e}")
        return jsonify({"status": "error", "message": str(e)})

@socketio.on('load_results')
def handle_load_results():
    logger.debug("Loading results")
    try:
        csv_path = "data/results/all_stage_results.csv"
        data = load_data(csv_path)
        logger.debug(f"Data loaded: {data}")
        standings = compute_standings(data)
        match_results, knockout_matches = organize_matches_by_group(data)

        emit('results_loaded', {
            'standings': standings.to_dict(orient='records'),
            'match_results': match_results,
            'knockout_matches': knockout_matches
        })
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        emit('error', {'message': str(e)})

if __name__ == "__main__":
    socketio.run(app, debug=True)
