from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pandas as pd
from collections import defaultdict
from scripts.standings_calculations import compute_standings
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

def load_data(csv_path):
    return pd.read_csv(csv_path, na_values=[''])

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
    return render_template("index.html")

def simulate_group_stage():
    # Simulate group stage matches and update
    # You should replace this with actual simulation logic
    matches = [
        {'team1': 'Team A', 'team2': 'Team B', 'team1_score': 1, 'team2_score': 0},
        {'team1': 'Team C', 'team2': 'Team D', 'team1_score': 2, 'team2_score': 2},
        # Add more matches as needed
    ]
    for match in matches:
        socketio.emit('match_update', match)
        time.sleep(1)  # Simulate some processing time

    # Example group standings (you should calculate this based on match results)
    standings = [
        {'team': 'Team A', 'points': 6},
        {'team': 'Team B', 'points': 3},
        {'team': 'Team C', 'points': 3},
        {'team': 'Team D', 'points': 0},
        # Add more standings as needed
    ]
    socketio.emit('group_stage_complete', {'standings': standings})

@socketio.on('start_simulation')
def handle_start_simulation():
    threading.Thread(target=simulate_group_stage).start()

if __name__ == "__main__":
    socketio.run(app, debug=True)
