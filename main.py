
from flask import Flask
import csv
import logging
import pandas as pd
from argparse import ArgumentParser
from flask_socketio import SocketIO, emit
from scripts.config import load_config
from scripts.calculations import perform_calculations
from scripts.group_match_calculations import simulate_group_stage_matches
from scripts.knockout_stage_calculations import simulate_knockout_stage, infer_next_round_fixtures, get_actual_teams
from scripts.standings_calculations import compute_standings
from scripts.data_transform import transform_data

app = Flask(__name__)
socketio = SocketIO(app)

# Configure logging
logger = logging.getLogger(__name__)

def run_predictor(debug=False):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config()
    teams = [team for group in config['teams'].values() for team in group]
    logger.info('Running Predictor')

    track_winners = {}


    perform_calculations(config, teams)

    for i in range(1000):

        # Simulate group stage matches
        simulate_group_stage(config, teams)

        # Process knockout stages
        winner = knockout_stage(config, teams)

        if winner in track_winners.keys():
            track_winners[winner] = track_winners[winner] + 1
            track_winners.update({winner: track_winners[winner] + 1})
        else:
            track_winners[winner] = 1

    with open('winners.csv', 'w') as csv_file:  
        csv_file = csv.writer(csv_file)
        for key, value in track_winners.items():
            csv_file.writerow([key, value])
    print(track_winners)
    


def simulate_group_stage(config, teams):
    from scripts.group_match_calculations import main as simulate_matches
    results = simulate_matches(config, teams)
    socketio.emit('group_stage_results', {'results': results.to_dict(orient='records')})

def knockout_stage(config, teams):
    standings = compute_standings_from_results()
    socketio.emit('group_stage_complete', {'standings': standings.to_dict(orient='records')})
    logger.info("Standings:\n%s", standings)

    round_of_16_fixtures = calculate_last_16_fixtures(standings)
    socketio.emit('knockout_stage_start', {'fixtures': round_of_16_fixtures})
    logger.info("Round of 16 Fixtures:\n%s", round_of_16_fixtures)

    config_vars = get_knockout_stage_config_vars(config, teams)
    

    all_knockout_results = pd.DataFrame()

    
    # Simulate Round of 16
    round_of_16_results = simulate_knockout_stage(round_of_16_fixtures, **config_vars, stage="Round of 16")
    all_knockout_results = pd.concat([all_knockout_results, round_of_16_results])
    socketio.emit('match_update', {'results': round_of_16_results.to_dict(orient='records')})

    quarter_final_fixtures = infer_next_round_fixtures(round_of_16_results, "Quarter-final")

    # Simulate Quarter Finals
    quarter_final_results = simulate_knockout_stage(quarter_final_fixtures, **config_vars, stage="Quarter-final")
    all_knockout_results = pd.concat([all_knockout_results, quarter_final_results])
    socketio.emit('match_update', {'results': quarter_final_results.to_dict(orient='records')})

    semi_final_fixtures = infer_next_round_fixtures(quarter_final_results, "Semi-final")

    # Simulate Semi Finals
    semi_final_results = simulate_knockout_stage(semi_final_fixtures, **config_vars, stage="Semi-final")
    all_knockout_results = pd.concat([all_knockout_results, semi_final_results])
    socketio.emit('match_update', {'results': semi_final_results.to_dict(orient='records')})

    final_fixtures = infer_next_round_fixtures(semi_final_results, "Final")

    # Simulate Final
    final_results = simulate_knockout_stage(final_fixtures, **config_vars, stage="Final")

    if((final_results.iloc[0]['team1_score'] > final_results.iloc[0]['team2_score']) or (final_results.iloc[0]['team1_pso_score'] > final_results.iloc[0]['team2_pso_score'])):
        
        winner = final_results.iloc[0]['team1']
    elif((final_results.iloc[0]['team1_score'] < final_results.iloc[0]['team2_score']) or (final_results.iloc[0]['team1_pso_score'] < final_results.iloc[0]['team2_pso_score'])):
        
        winner = final_results.iloc[0]['team2']


    all_knockout_results = pd.concat([all_knockout_results, final_results])
    socketio.emit('match_update', {'results': final_results.to_dict(orient='records')})

    # Save all knockout results to CSV
    all_knockout_results.to_csv('data/results/knockout_stage_results.csv', index=False)
    logger.info("All knockout stage results saved to data/results/knockout_stage_results.csv")

    return  winner

def compute_standings_from_results():
    data = pd.read_csv('data/results/group_stage_results.csv')
    standings = compute_standings(data)
    return standings

def calculate_last_16_fixtures(standings):
    fixtures = []
    dtype = {'team1': str, 'team2': str}
    column_names = ['stage', 'date', 'time', 'venue', 'team1', 'team1_score', 'team2', 'team2_score', 'team1_pso_score', 'team2_pso_score']
    # Read the CSV file with specified column names, forcing all columns to be read as strings
    knockout_schedule = pd.read_csv('data/raw/knockout_match_schedule.csv', names=column_names, skiprows=1, dtype=str)
    logger.debug("Knockout_schedule:\n%s", knockout_schedule)
    actual_teams = get_actual_teams(standings)
    logger.debug("Actual Teams After Mapping:\n%s", actual_teams)

    for _, match in knockout_schedule.iterrows():
        original_team1 = match['team1']
        original_team2 = match['team2']
        
        team1 = actual_teams.get(original_team1, original_team1)
        team2 = actual_teams.get(original_team2, original_team2)
        
        # Add debugging information
        logger.debug(f"Original Team1: {original_team1}, Mapped Team1: {team1}")
        logger.debug(f"Original Team2: {original_team2}, Mapped Team2: {team2}")

        # Handling placeholders dynamically
        if '/' in team1:
            team1 = resolve_placeholder(team1, actual_teams)
        if '/' in team2:
            team2 = resolve_placeholder(team2, actual_teams)
        
        fixtures.append({'team1': team1, 'team2': team2, 'stage': match['stage'], 'date': match['date'], 'time': match['time'], 'venue': match['venue']})

    logger.debug("Fixtures for Round of 16:\n%s", fixtures)

    return fixtures

def resolve_placeholder(placeholder, actual_teams):
    options = placeholder.split('/')
    for option in options:
        if option in actual_teams:
            return actual_teams[option]
    return placeholder  # Default to placeholder if no match is found

def get_knockout_stage_config_vars(config, teams):
    match_schedule_path = 'data/raw/group_match_schedule.csv'
    win_percentages_path = 'data/tmp/euro_teams_win_percentage.csv'

    # Load win percentages
    win_percentages = pd.read_csv(win_percentages_path)
    win_percentages_dict = dict(zip(win_percentages['team'].str.strip().str.upper(), win_percentages['win_percentage']))

    home_advantage = config.get('home_advantage', 0)
    home_team = config.get('home_team', '').strip().upper()
    weighted_win_percentage_weight = config.get('weighted_win_percentage_weight', 1.0)  # Default to 1.0 if not specified

    # Calculate averages from historical data
    historical_data_path = 'data/raw/results.csv'
    historical_data = pd.read_csv(historical_data_path)
    look_back_months = config['look_back_months']
    _, averages = transform_data(historical_data, teams, look_back_months)

    return {
        'config': config,
        'teams': teams,
        'win_percentages': win_percentages_dict,
        'averages': averages,
        'home_advantage': home_advantage,
        'home_team': home_team,
        'weighted_win_percentage_weight': weighted_win_percentage_weight
    }

def concatenate_results(group_stage_path, knockout_stage_path, output_path):
    # Load group stage results
    group_stage_results = pd.read_csv(group_stage_path)
    
    # Load knockout stage results
    knockout_stage_results = pd.read_csv(knockout_stage_path)
    
    # Concatenate the results
    all_results = pd.concat([group_stage_results, knockout_stage_results], ignore_index=True)
    
    # Save the concatenated results to a new CSV file
    all_results.to_csv(output_path, index=False)
    print(f"Concatenated results saved to {output_path}")

# Define file paths
group_stage_path = 'data/results/group_stage_results.csv'
knockout_stage_path = 'data/results/knockout_stage_results.csv'
output_path = 'data/results/all_stage_results.csv'

# Concatenate the results
concatenate_results(group_stage_path, knockout_stage_path, output_path)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    run_predictor(debug=args.debug)
