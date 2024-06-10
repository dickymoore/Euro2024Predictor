import pandas as pd
import numpy as np
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

def load_match_schedule(file_path):
    return pd.read_csv(file_path)

def calculate_goal_probability(win_percentage):
    goals_per_game = 2.5  # Average goals per game assumption
    goal_probability_per_minute = (win_percentage / 100) * (goals_per_game / 90)
    return goal_probability_per_minute

def simulate_match_minute_by_minute(team1, team2, team1_win_percentage, team2_win_percentage, home_advantage, home_team):
    team1_goals = 0
    team2_goals = 0

    team1_goal_prob = calculate_goal_probability(team1_win_percentage + (home_advantage if team1 == home_team else 0))
    team2_goal_prob = calculate_goal_probability(team2_win_percentage + (home_advantage if team2 == home_team else 0))

    for minute in range(90):
        if np.random.rand() < team1_goal_prob:
            team1_goals += 1
        if np.random.rand() < team2_goal_prob:
            team2_goals += 1

    return team1_goals, team2_goals

def simulate_group_stage_matches(matches, win_percentages, home_advantage, home_team):
    results = []
    for index, match in tqdm(matches.iterrows(), total=matches.shape[0], desc="Simulating Matches"):
        team1 = match['team1']
        team2 = match['team2']
        venue = match['venue']
        date = match['date']
        time = match['time']
        group = match['group']
        stage = match['stage']

        team1_win_percentage = win_percentages.get(team1, 50)
        team2_win_percentage = win_percentages.get(team2, 50)

        team1_score, team2_score = simulate_match_minute_by_minute(
            team1, team2, team1_win_percentage, team2_win_percentage, home_advantage, home_team
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
            'team1_pso_score': '',  # Placeholder for penalty shootout scores if needed
            'team2_pso_score': ''
        })
    return pd.DataFrame(results)

def main():
    config_path = 'config/config.yaml'
    match_schedule_path = 'data/raw/group_match_schedule.csv'
    win_percentages_path = 'data/tmp/euro_teams_win_percentage.csv'
    output_path = 'data/results/group_stage_results.csv'

    # Load configuration
    from scripts.config import load_config
    config = load_config(config_path)

    # Load match schedule
    matches = load_match_schedule(match_schedule_path)

    # Load win percentages
    win_percentages_df = pd.read_csv(win_percentages_path)
    win_percentages = dict(zip(win_percentages_df['team'], win_percentages_df['win_percentage']))

    home_advantage = config.get('home_advantage', 0)
    home_team = config.get('home_team', '')

    # Simulate matches
    results = simulate_group_stage_matches(matches, win_percentages, home_advantage, home_team)

    # Save results
    results.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
