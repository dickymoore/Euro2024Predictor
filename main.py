import logging
import pandas as pd
from argparse import ArgumentParser
from scripts.config import load_config
from scripts.calculations import perform_calculations
from scripts.group_match_calculations import simulate_group_stage_matches
from scripts.knockout_stage_calculations import simulate_knockout_stage, infer_next_round_fixtures
from scripts.standings_calculations import compute_standings  # Ensure compute_standings is imported
from scripts.data_transform import transform_data  # Import transform_data function

# Configure logging
logger = logging.getLogger(__name__)

def main(debug=False):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = load_config()
    teams = [team for group in config['teams'].values() for team in group]
    logger.info('Running Predictor')
    
    perform_calculations(config, teams)
    
    # Simulate group stage matches
    simulate_group_stage(config, teams)
    
    # Process knockout stages
    knockout_stage(config, teams)

def simulate_group_stage(config, teams):
    from scripts.group_match_calculations import main as simulate_matches
    simulate_matches(config, teams)
    
def knockout_stage(config, teams):
    standings = compute_standings_from_results()
    round_of_16_fixtures = calculate_last_16_fixtures(standings)
    config_vars = get_knockout_stage_config_vars(config, teams)
    
    all_knockout_results = pd.DataFrame()

    # Simulate Round of 16
    round_of_16_results = simulate_knockout_stage(round_of_16_fixtures, **config_vars, stage="Round of 16")
    all_knockout_results = pd.concat([all_knockout_results, round_of_16_results])
    quarter_final_fixtures = infer_next_round_fixtures(round_of_16_results)
    
    # Simulate Quarter Finals
    quarter_final_results = simulate_knockout_stage(quarter_final_fixtures, **config_vars, stage="Quarter-final")
    all_knockout_results = pd.concat([all_knockout_results, quarter_final_results])
    semi_final_fixtures = infer_next_round_fixtures(quarter_final_results)
    
    # Simulate Semi Finals
    semi_final_results = simulate_knockout_stage(semi_final_fixtures, **config_vars, stage="Semi-final")
    all_knockout_results = pd.concat([all_knockout_results, semi_final_results])
    final_fixtures = infer_next_round_fixtures(semi_final_results)
    
    # Simulate Final
    final_results = simulate_knockout_stage(final_fixtures, **config_vars, stage="Final")
    all_knockout_results = pd.concat([all_knockout_results, final_results])

    # Save all knockout results to CSV
    all_knockout_results.to_csv('data/results/knockout_stage_results.csv', index=False)
    logger.info(f"All knockout stage results saved to data/results/knockout_stage_results.csv")

def compute_standings_from_results():
    data = pd.read_csv('data/results/group_stage_results.csv')
    standings = compute_standings(data)
    return standings

def calculate_last_16_fixtures(standings):
    fixtures = []
    
    # Assume top 2 teams from each group qualify
    qualified_teams = standings[standings['qualified'] == 'qualified'].sort_values(by=['group', 'points', 'gd', 'gf'])
    
    # Best 4 third-placed teams
    best_third_teams = standings[standings['qualified'] == 'best-third'].sort_values(by=['points', 'gd', 'gf']).head(4)
    
    # Combine top teams and best third-placed teams
    all_qualified_teams = pd.concat([qualified_teams, best_third_teams])
    
    # Create fixtures (this is a simplified version and can be adjusted as per the actual tournament structure)
    groups = all_qualified_teams['group'].unique()
    for i in range(0, len(groups), 2):
        if i + 1 < len(groups):
            group1_teams = all_qualified_teams[all_qualified_teams['group'] == groups[i]]
            group2_teams = all_qualified_teams[all_qualified_teams['group'] == groups[i + 1]]
            
            fixtures.append({'team1': group1_teams.iloc[0]['team'], 'team2': group2_teams.iloc[1]['team']})
            fixtures.append({'team1': group2_teams.iloc[0]['team'], 'team2': group1_teams.iloc[1]['team']})
            if len(group1_teams) > 2:
                fixtures.append({'team1': group1_teams.iloc[2]['team'], 'team2': best_third_teams.iloc[i % 4]['team']})
            if len(group2_teams) > 2:
                fixtures.append({'team1': group2_teams.iloc[2]['team'], 'team2': best_third_teams.iloc[(i + 1) % 4]['team']})
    
    return fixtures

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

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    main(debug=args.debug)
