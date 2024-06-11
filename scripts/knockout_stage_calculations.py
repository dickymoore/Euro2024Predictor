import pandas as pd
import numpy as np
import logging
from scripts.data_transform import transform_data
from scripts.config import load_config
from scripts.standings_calculations import compute_standings

logger = logging.getLogger(__name__)

def simulate_knockout_stage(fixtures, config, teams, win_percentages, averages, home_advantage, home_team, weighted_win_percentage_weight, stage):
    results = []
    for match in fixtures:
        team1 = match['team1']
        team2 = match['team2']
        
        logger.info(f"Simulating match: {team1} vs {team2}")
        
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

        team1_pen_score, team2_pen_score = None, None
        if team1_score == team2_score:
            team1_pen_score, team2_pen_score = simulate_penalty_shootout()

        logger.info(f"{team1} vs {team2} -> {team1_score}-{team2_score}")

        results.append({
            'stage': stage,
            'team1': team1,
            'team1_score': team1_score,
            'team2': team2,
            'team2_score': team2_score,
            'team1_pso_score': team1_pen_score,
            'team2_pso_score': team2_pen_score
        })
    
    return pd.DataFrame(results)

def calculate_goal_probability(win_percentage, avg_goals_scored, avg_goals_conceded, weighted_win_percentage_weight):
    base_goals_per_game = 2.5
    goals_per_game = (avg_goals_scored + avg_goals_conceded) / 2
    goal_probability_per_minute = (win_percentage / 100) * (goals_per_game / 90) * weighted_win_percentage_weight
    return goal_probability_per_minute

def simulate_match_minute_by_minute(team1, team2, team1_win_percentage, team2_win_percentage, home_advantage, home_team, averages, weighted_win_percentage_weight):
    team1_goals = 0
    team2_goals = 0

    team1_avg_goals_scored = averages.at[team1, 'average_goals_scored']
    team1_avg_goals_conceded = averages.at[team1, 'average_goals_conceded']
    team2_avg_goals_scored = averages.at[team2, 'average_goals_scored']
    team2_avg_goals_conceded = averages.at[team2, 'average_goals_conceded']

    team1_goal_prob = calculate_goal_probability(
        team1_win_percentage + (home_advantage if team1 == home_team else 0),
        team1_avg_goals_scored, team2_avg_goals_conceded, weighted_win_percentage_weight
    )
    team2_goal_prob = calculate_goal_probability(
        team2_win_percentage + (home_advantage if team2 == home_team else 0),
        team2_avg_goals_scored, team1_avg_goals_conceded, weighted_win_percentage_weight
    )

    for minute in range(90):
        if np.random.rand() < team1_goal_prob:
            team1_goals += 1
        if np.random.rand() < team2_goal_prob:
            team2_goals += 1

    return team1_goals, team2_goals

def simulate_penalty_shootout():
    team1_pen_score = 0
    team2_pen_score = 0
    for _ in range(5):
        if np.random.rand() > 0.5:
            team1_pen_score += 1
        if np.random.rand() > 0.5:
            team2_pen_score += 1
    
    while team1_pen_score == team2_pen_score:
        if np.random.rand() > 0.5:
            team1_pen_score += 1
        if np.random.rand() > 0.5:
            team2_pen_score += 1

    return team1_pen_score, team2_pen_score

def infer_next_round_fixtures(results, next_stage):
    # Determine the winners from the current round results
    winners = []
    for _, match in results.iterrows():
        if match['team1_score'] > match['team2_score']:
            winners.append(match['team1'])
        elif match['team1_score'] < match['team2_score']:
            winners.append(match['team2'])
        else:
            # Assuming penalties decide the winner in case of a draw
            if match['team1_pso_score'] > match['team2_pso_score']:
                winners.append(match['team1'])
            else:
                winners.append(match['team2'])
    
    # Pair up the winners for the next round fixtures
    next_round_fixtures = []
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            next_round_fixtures.append({
                'team1': winners[i],
                'team2': winners[i + 1],
                'stage': next_stage,
                'date': None,  # Dates can be filled in if available
                'time': None,  # Times can be filled in if available
                'venue': None  # Venues can be filled in if available
            })
    
    return next_round_fixtures

def get_actual_teams(standings):
    actual_teams = {}
    
    # Determine the top 2 teams from each group
    for group in standings['group'].unique():
        group_standings = standings[standings['group'] == group].sort_values(by=['points', 'gd', 'gf'], ascending=[False, False, False])
        top_two = group_standings.head(2)
        if not top_two.empty:
            actual_teams[f'1{group}'] = top_two.iloc[0]['team']
            actual_teams[f'2{group}'] = top_two.iloc[1]['team']
            print(f"Group {group}: 1st {actual_teams[f'1{group}']}, 2nd {actual_teams[f'2{group}']}")
        else:
            print(f"Group {group} standings data is empty or not found.")
    
    # Determine the best third-placed teams
    third_place_teams = standings.groupby('group').nth(2)
    best_third_teams = third_place_teams.sort_values(by=['points', 'gd', 'gf'], ascending=[False, False, False]).head(4)

    third_place_keys = ['3A', '3B', '3C', '3D']  # Adjust the keys according to your knockout schedule placeholders

    # Assign the best third-placed teams to their respective placeholders
    for key, value in zip(third_place_keys, best_third_teams['team']):
        actual_teams[key] = value
        print(f"Best third-placed team {key}: {value}")

    print("Actual Teams:\n", actual_teams)
    return actual_teams

def main():
    config = load_config()
    teams = [team for group in config['teams'].values() for team in group]
    
    standings = compute_standings_from_results()
    round_of_16_fixtures = calculate_last_16_fixtures(standings)
    config_vars = get_knockout_stage_config_vars(config, teams)

    all_knockout_results = pd.DataFrame()

    # Simulate Round of 16
    round_of_16_results = simulate_knockout_stage(round_of_16_fixtures, config, teams, **config_vars, stage="Round of 16")
    all_knockout_results = pd.concat([all_knockout_results, round_of_16_results])
    quarter_final_fixtures = infer_next_round_fixtures(round_of_16_results, "Quarter-final")
    
    # Simulate Quarter Finals
    quarter_final_results = simulate_knockout_stage(quarter_final_fixtures, config, teams, **config_vars, stage="Quarter-final")
    all_knockout_results = pd.concat([all_knockout_results, quarter_final_results])
    semi_final_fixtures = infer_next_round_fixtures(quarter_final_results, "Semi-final")
    
    # Simulate Semi Finals
    semi_final_results = simulate_knockout_stage(semi_final_fixtures, config, teams, **config_vars, stage="Semi-final")
    all_knockout_results = pd.concat([all_knockout_results, semi_final_results])
    final_fixtures = infer_next_round_fixtures(semi_final_results, "Final")
    
    # Simulate Final
    final_results = simulate_knockout_stage(final_fixtures, config, teams, **config_vars, stage="Final")
    all_knockout_results = pd.concat([all_knockout_results, final_results])

    # Save all knockout results to CSV
    all_knockout_results.to_csv('data/results/knockout_stage_results.csv', index=False)
    logger.info(f"All knockout stage results saved to data/results/knockout_stage_results.csv")

if __name__ == "__main__":
    main()
