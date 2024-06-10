import pandas as pd
import numpy as np
from tqdm import tqdm
import logging
import os

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def load_match_schedule(file_path):
    return pd.read_csv(file_path)

def calculate_match_outcome(team1, team2, team1_win_percentage, team2_win_percentage, home_team, home_advantage):
    if team1 == home_team:
        team1_win_percentage += home_advantage
    elif team2 == home_team:
        team2_win_percentage += home_advantage

    total_percentage = team1_win_percentage + team2_win_percentage
    team1_prob = team1_win_percentage / total_percentage
    team2_prob = team2_win_percentage / total_percentage

    if np.random.rand() <= team1_prob:
        team1_score = np.random.randint(1, 4)
        team2_score = max(0, team1_score - np.random.randint(1, 3))
    else:
        team2_score = np.random.randint(1, 4)
        team1_score = max(0, team2_score - np.random.randint(1, 3))

    return team1_score, team2_score

def simulate_group_stage_matches(matches, win_percentages, home_team, home_advantage):
    results = []
    for index, match in tqdm(matches.iterrows(), total=matches.shape[0], desc="Simulating Matches"):
        team1 = match['team1']
        team2 = match['team2']
        venue = match['venue']
        date = match['date']
        time = match['time']
        stage = match['stage']
        group = match['group']

        team1_win_percentage = win_percentages.get(team1, 50)
        team2_win_percentage = win_percentages.get(team2, 50)

        team1_score, team2_score = calculate_match_outcome(
            team1, team2, team1_win_percentage, team2_win_percentage, home_team, home_advantage
        )

        logger.info(f"{date} {time} - {venue}: {team1} vs {team2} -> {team1_score}-{team2_score}")

        results.append({
            'stage': stage,
            'group': group,
            'date': date,
            'time': time,
            'venue': venue,
            'team1': team1,
            'team1_score': team1_score,
            'team2': team2,
            'team2_score': team2_score,
            'team1_pso_score': '',
            'team2_pso_score': ''
        })
    return pd.DataFrame(results)

def load_win_percentages():
    win_percentage_path = 'data/tmp/euro_teams_win_percentage.csv'
    win_percentages = pd.read_csv(win_percentage_path)
    win_percentages_dict = win_percentages.set_index('team')['win_percentage'].to_dict()
    return win_percentages_dict

def main():
    config_path = 'config/config.yaml'
    match_schedule_path = 'data/raw/group_match_schedule.csv'
    output_path = 'data/results/group_stage_results.csv'
    output_directory = os.path.dirname(output_path)

    # Load configuration
    from scripts.config import load_config
    config = load_config(config_path)

    # Load match schedule
    matches = load_match_schedule(match_schedule_path)

    # Load win percentages
    win_percentages = load_win_percentages()

    home_advantage = config.get('home_advantage', 0)
    home_team = config.get('home_team', '')

    # Ensure the output directory exists
    ensure_directory_exists(output_directory)

    # Simulate matches
    results = simulate_group_stage_matches(matches, win_percentages, home_team, home_advantage)

    # Save results in the specified format
    results.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
