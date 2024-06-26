import pandas as pd
import numpy as np
from tqdm import tqdm
import logging
from scripts.data_transform import transform_data
import logging
from scripts.logger_config import logger  # Import centralized logger

def load_match_schedule(file_path):
    return pd.read_csv(file_path)

def load_win_percentages(file_path):
    win_percentage_df = pd.read_csv(file_path)
    return dict(zip(win_percentage_df['team'].str.strip().str.upper(), win_percentage_df['win_percentage']))

def calculate_goal_probability(win_percentage, avg_goals_scored, avg_goals_conceded, weighted_win_percentage_weight):
    base_goals_per_game = 2.5
    goals_per_game = (avg_goals_scored + avg_goals_conceded) / 2
    goal_probability_per_minute = (win_percentage / 100) * (goals_per_game / 90) * weighted_win_percentage_weight
    return goal_probability_per_minute

def simulate_match_minute_by_minute(team1, team2, team1_win_percentage, team2_win_percentage, home_advantage, home_team, averages, weighted_win_percentage_weight):
    logger.debug(f"Simulating match between {team1} and {team2}")
    logger.debug(f"Initial win percentages - {team1}: {team1_win_percentage}%, {team2}: {team2_win_percentage}%")
    
    team1_goals = 0
    team2_goals = 0

    team1_avg_goals_scored = averages.at[team1, 'average_goals_scored']
    team1_avg_goals_conceded = averages.at[team1, 'average_goals_conceded']
    team2_avg_goals_scored = averages.at[team2, 'average_goals_scored']
    team2_avg_goals_conceded = averages.at[team2, 'average_goals_conceded']

    logger.debug(f"{team1} - Avg Goals Scored: {team1_avg_goals_scored}, Avg Goals Conceded: {team1_avg_goals_conceded}")
    logger.debug(f"{team2} - Avg Goals Scored: {team2_avg_goals_scored}, Avg Goals Conceded: {team2_avg_goals_conceded}")

    team1_goal_prob = calculate_goal_probability(
        team1_win_percentage + (home_advantage if team1 == home_team else 0),
        team1_avg_goals_scored, team2_avg_goals_conceded, weighted_win_percentage_weight
    )
    team2_goal_prob = calculate_goal_probability(
        team2_win_percentage + (home_advantage if team2 == home_team else 0),
        team2_avg_goals_scored, team1_avg_goals_conceded, weighted_win_percentage_weight
    )

    logger.debug(f"{team1} goal probability per minute: {team1_goal_prob}")
    logger.debug(f"{team2} goal probability per minute: {team2_goal_prob}")

    logger.debug(f"Minute 00: Kick off! Current score - {team1}: {team1_goals}, {team2}: {team2_goals}")

    for minute in range(90):
        if np.random.rand() < team1_goal_prob:
            team1_goals += 1
            logger.debug(f"Minute {minute}: {team1} scores! Current score - {team1}: {team1_goals}, {team2}: {team2_goals}")
        elif np.random.rand() < team2_goal_prob:
            team2_goals += 1
            logger.debug(f"Minute {minute}: {team2} scores! Current score - {team1}: {team1_goals}, {team2}: {team2_goals}")
        elif minute % 5 == 0:
            # Log a dot for each minute without a goal
            logger.debug(f"Minute {minute}")

    logger.debug(f"Final score for match {team1} vs {team2}: {team1_goals} - {team2_goals}")
    return team1_goals, team2_goals

def simulate_group_stage_matches(matches, win_percentages, home_advantage, home_team, averages, weighted_win_percentage_weight):
    results = []
    for index, match in tqdm(matches.iterrows(), total=matches.shape[0], desc="Simulating Matches"):
        team1 = match['team1'].strip().upper()
        team2 = match['team2'].strip().upper()
        venue = match['venue']
        date = match['date']
        time = match['time']
        group = match['group']
        stage = match['stage']

        team1_win_percentage = win_percentages.get(team1, 50)
        team2_win_percentage = win_percentages.get(team2, 50)

        if team1 not in averages.index:
            logger.error(f"Team {team1} not found in averages")
            continue
        if team2 not in averages.index:
            logger.error(f"Team {team2} not found in averages")
            continue

        team1_score, team2_score = simulate_match_minute_by_minute(
            team1, team2, team1_win_percentage, team2_win_percentage, home_advantage, home_team, averages, weighted_win_percentage_weight
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

def main(config, teams):
    match_schedule_path = 'data/raw/group_match_schedule.csv'
    win_percentages_path = 'data/tmp/euro_teams_win_percentage.csv'
    output_path = 'data/results/group_stage_results.csv'

    # Load match schedule and win percentages
    matches = load_match_schedule(match_schedule_path)
    win_percentages = load_win_percentages(win_percentages_path)

    home_advantage = config.get('home_advantage', 0)
    home_team = config.get('home_team', '').strip().upper()
    weighted_win_percentage_weight = config.get('weighted_win_percentage_weight', 1.0)  # Default to 1.0 if not specified

    # Calculate averages from historical data
    historical_data_path = 'data/raw/results.csv'
    historical_data = pd.read_csv(historical_data_path)
    look_back_months = config['look_back_months']
    _, averages = transform_data(historical_data, teams, look_back_months)

    # Check contents of averages
    logger.debug(f"Averages DataFrame: \n{averages}")

    # Simulate matches
    results = simulate_group_stage_matches(matches, win_percentages, home_advantage, home_team, averages, weighted_win_percentage_weight)

    # Save results
    results.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

    return results

if __name__ == "__main__":
    from scripts.config import load_config
    config = load_config()
    teams = [team for group in config['teams'].values() for team in group]
    main(config, teams)
