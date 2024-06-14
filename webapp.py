from flask import Flask, render_template, request, jsonify
import pandas as pd
import threading
import yaml
import logging
import os
import subprocess
from collections import defaultdict
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
calculations_complete_event = threading.Event()

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

@app.route("/status", methods=["GET"])
def check_status():
    # Implement logic to check if the process is complete
    is_complete = check_if_process_is_complete()
    return jsonify({"status": "complete" if is_complete else "running"})

@app.route("/")
def index():
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

    return render_template(
        "index.html", 
        match_results=match_results, 
        standings=standings, 
        knockout_matches=knockout_matches
    )

@app.route("/run_predictor", methods=["POST"])
def run_predictor():
    try:
        data = request.get_json()
        weighted_win_percentage_weight = data.get('weighted_win_percentage_weight', 1)
        home_advantage = data.get('home_advantage', 0.1)
        look_back_months = data.get('look_back_months', 36)

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.yaml')

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        config['weighted_win_percentage_weight'] = float(weighted_win_percentage_weight)
        config['home_advantage'] = float(home_advantage)
        config['look_back_months'] = int(look_back_months)

        with open(config_path, 'w') as file:
            yaml.safe_dump(config, file)

        # Start the script in a new thread
        threading.Thread(target=run_main_script).start()

        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error in run_predictor: {e}")
        return jsonify({"status": "error", "message": str(e)})

def run_main_script():
    try:
        logger.debug("Starting main.py subprocess")

        # Determine the correctf path to the Python interpreter in the virtual environment
        virtual_env = os.getenv('VIRTUAL_ENV')
        if virtual_env:
            if os.name == 'nt':  # Windows
                python_executable = os.path.join(virtual_env, 'Scripts', 'python.exe')
            else:  # Unix or Mac
                python_executable = os.path.join(virtual_env, 'bin', 'python')
        else:
            python_executable = 'python'

        script_path = os.path.abspath("main.py")

        logger.debug(f"Using Python executable: {python_executable}")
        logger.debug(f"Running script at: {script_path}")

        process = subprocess.Popen(
            [python_executable, script_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            bufsize=1
        )
        logger.debug("Subprocess start attempt made")

        while True:
            logger.debug("In loop")
            exit()
            stdout_line = process.stdout.readline()
            # if not stdout_line and process.poll() is not None:
            #     break
            
            logger.debug("looping")
            exit() # this isn't being hit.
            
            if stdout_line:
                logger.info(stdout_line.strip())
                if "Calculations complete" in stdout_line:
                    logger.debug("Detected 'Calculations complete' in the subprocess output")
                    calculations_complete_event.set()  # Signal that calculations are complete
                    # break

        process.stdout.close()
        process.wait()
        logger.debug(f"Subprocess exited with return code: {process.returncode}")

        if process.returncode != 0:
            stderr_output = process.stderr.read()
            logger.error(f"Subprocess exited with errors: {stderr_output}")
        process.stderr.close()

    except Exception as e:
        logger.error(f"Exception occurred while running the main script: {e}")


if __name__ == "__main__":
        app.run(debug=True)