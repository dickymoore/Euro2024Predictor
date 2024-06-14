import argparse
import sys
import logging
import os
import pandas as pd
from scripts.config import load_config
from scripts.calculations import perform_calculations
from scripts.group_match_calculations import main as simulate_group_stage_matches
from scripts.knockout_stage_calculations import simulate_knockout_stage, infer_next_round_fixtures, get_actual_teams
from scripts.standings_calculations import compute_standings
from scripts.data_transform import transform_data

sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.FileHandler('data/tmp/predictor.log')
formatter = logging.Formatter('%(asctime)s - %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
# Clear the predictor.log file
predictor_log_path = os.path.abspath("predictor.log")
with open(predictor_log_path, 'w'):
    pass
logger.debug("Cleared predictor.log file")


def run_predictor(debug=False):
    logger.debug('Running run_predictor')
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.debug)
    try:
        config = load_config()
        teams = [team for group in config['teams'].values() for team in group]
        logger.debug('Running Predictor')

        perform_calculations(config, teams)
        logger.debug('Completed perform_calculations')

        # Simulate group stage matches
        simulate_group_stage(config, teams) # matches, win_percentages, home_advantage, home_team, averages, weighted_win_percentage_weight
        logger.debug('Completed simulate_group_stage')

        # Process knockout stages
        knockout_stage(config, teams)
        logger.debug('Completed knockout_stage')
    except Exception as e:
        logger.error(f"Error in run_predictor: {e}")

def simulate_group_stage(config, teams):
    logger.debug('Running simulate_group_stage')
    results = simulate_group_stage_matches(config, teams)
    logger.debug('results = simulate_group_stage_matches(config, teams)')
    logger.debug('Simulated group stage matches')

def knockout_stage(config, teams):
    logger.debug('Running knockout_stage')
    standings = compute_standings_from_results()
    logger.debug("Standings:\n%s", standings)

    round_of_16_fixtures = calculate_last_16_fixtures(standings)
    logger.debug("Round of 16 Fixtures:\n%s", round_of_16_fixtures)

    config_vars = get_knockout_stage_config_vars(config, teams)

    all_knockout_results = pd.DataFrame()

    # Simulate Round of 16
    round_of_16_results = simulate_knockout_stage(round_of_16_fixtures, **config_vars, stage="Round of 16")
    all_knockout_results = pd.concat([all_knockout_results, round_of_16_results])
    logger.debug('Simulated Round of 16')

    quarter_final_fixtures = infer_next_round_fixtures(round_of_16_results, "Quarter-final")

    # Simulate Quarter Finals
    quarter_final_results = simulate_knockout_stage(quarter_final_fixtures, **config_vars, stage="Quarter-final")
    all_knockout_results = pd.concat([all_knockout_results, quarter_final_results])
    logger.debug('Simulated Quarter-finals')

    semi_final_fixtures = infer_next_round_fixtures(quarter_final_results, "Semi-final")

    # Simulate Semi Finals
    semi_final_results = simulate_knockout_stage(semi_final_fixtures, **config_vars, stage="Semi-final")
    all_knockout_results = pd.concat([all_knockout_results, semi_final_results])
    logger.debug('Simulated Semi-finals')

    final_fixtures = infer_next_round_fixtures(semi_final_results, "Final")

    # Simulate Final
    final_results = simulate_knockout_stage(final_fixtures, **config_vars, stage="Final")
    all_knockout_results = pd.concat([all_knockout_results, final_results])
    logger.debug('Simulated Final')

    # Save all knockout results to CSV
    all_knockout_results.to_csv('data/results/knockout_stage_results.csv', index=False)
    logger.debug("All knockout stage results saved to data/results/knockout_stage_results.csv")

def compute_standings_from_results():
    logger.debug('Running compute_standings_from_results')
    data = pd.read_csv('data/results/group_stage_results.csv')
    standings = compute_standings(data)
    return standings

def calculate_last_16_fixtures(standings):
    logger.debug('Running calculate_last_16_fixtures')
    fixtures = []
    dtype = {'team1': str, 'team2': str}
    column_names = ['stage', 'date', 'time', 'venue', 'team1', 'team1_score', 'team2', 'team2_score', 'team1_pso_score', 'team2_pso_score']
    knockout_schedule = pd.read_csv('data/raw/knockout_match_schedule.csv', names=column_names, skiprows=1, dtype=str)
    logger.debug("Knockout_schedule:\n%s", knockout_schedule)
    actual_teams = get_actual_teams(standings)
    logger.debug("Actual Teams After Mapping:\n%s", actual_teams)

    for _, match in knockout_schedule.iterrows():
        original_team1 = match['team1']
        original_team2 = match['team2']
        
        team1 = actual_teams.get(original_team1, original_team1)
        team2 = actual_teams.get(original_team2, original_team2)
        
        if '/' in team1:
            team1 = resolve_placeholder(team1, actual_teams)
        if '/' in team2:
            team2 = resolve_placeholder(team2, actual_teams)
        
        fixtures.append({'team1': team1, 'team2': team2, 'stage': match['stage'], 'date': match['date'], 'time': match['time'], 'venue': match['venue']})

    logger.debug("Fixtures for Round of 16:\n%s", fixtures)
    return fixtures

def resolve_placeholder(placeholder, actual_teams):
    logger.debug('Running resolve_placeholder')
    options = placeholder.split('/')
    for option in options:
        if option in actual_teams:
            return actual_teams[option]
    return placeholder

def get_knockout_stage_config_vars(config, teams):
    logger.debug('Running get_knockout_stage_config_vars')
    match_schedule_path = 'data/raw/group_match_schedule.csv'
    win_percentages_path = 'data/tmp/euro_teams_win_percentage.csv'

    win_percentages = pd.read_csv(win_percentages_path)
    win_percentages_dict = dict(zip(win_percentages['team'].str.strip().str.upper(), win_percentages['win_percentage']))

    home_advantage = config.get('home_advantage', 0)
    home_team = config.get('home_team', '').strip().upper()
    weighted_win_percentage_weight = config.get('weighted_win_percentage_weight', 1.0)

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
    logger.debug('Running concatenate_results')
    if os.path.exists(group_stage_path) and os.path.getsize(group_stage_path) > 0:
        group_stage_results = pd.read_csv(group_stage_path)
    else:
        group_stage_columns = ['stage', 'group', 'date', 'time', 'venue', 'team1', 'team1_score', 'team2', 'team2_score', 'team1_pso_score', 'team2_pso_score']
        group_stage_results = pd.DataFrame(columns=group_stage_columns)
        print(f"{group_stage_path} not found. Creating placeholder data.")

    if os.path.exists(knockout_stage_path) and os.path.getsize(knockout_stage_path) > 0:
        knockout_stage_results = pd.read_csv(knockout_stage_path)
    else:
        knockout_stage_columns = ['stage', 'team1', 'team1_score', 'team2', 'team2_score', 'team1_pso_score', 'team2_pso_score']
        knockout_stage_results = pd.DataFrame(columns=knockout_stage_columns)
        print(f"{knockout_stage_path} not found. Creating placeholder data.")

    all_results = pd.concat([group_stage_results, knockout_stage_results])
    all_results.to_csv(output_path, index=False)
    print(f"Concatenated results saved to {output_path}")
    logger.debug('Calculations complete')

def main():
    logger.debug('Running main')
    parser = argparse.ArgumentParser(description='Euro 2024 Predictor')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    run_predictor(debug=args.debug)
    concatenate_results('data/results/group_stage_results.csv', 'data/results/knockout_stage_results.csv', 'data/results/all_stage_results.csv')
    logger.debug('End of main')
    print("End of main")

# Run the predictor in standalone mode
if __name__ == "__main__":
    main()
