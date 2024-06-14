from collections import defaultdict
import pandas as pd
import logging
from scripts.logger_config import logger  # Import centralized logger

def compute_standings(data):
    logger.debug("Starting compute_standings function.")
    standings = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for _, row in data.iterrows():
        if row['stage'] != 'Group Stage':
            continue

        group = row['group']
        team1 = row['team1']
        team2 = row['team2']
        team1_score = int(row['team1_score'])
        team2_score = int(row['team2_score'])

        logger.debug(f"Processing match: {team1} vs {team2}, score: {team1_score}-{team2_score}")

        if team1_score > team2_score:
            standings[group][team1]['points'] += 3
            standings[group][team1]['w'] += 1
            standings[group][team2]['l'] += 1
            logger.debug(f"{team1} won. Updated standings: {team1} points: {standings[group][team1]['points']}, {team2} points: {standings[group][team2]['points']}")
        elif team1_score < team2_score:
            standings[group][team2]['points'] += 3
            standings[group][team2]['w'] += 1
            standings[group][team1]['l'] += 1
            logger.debug(f"{team2} won. Updated standings: {team2} points: {standings[group][team2]['points']}, {team1} points: {standings[group][team1]['points']}")
        else:
            standings[group][team1]['points'] += 1
            standings[group][team2]['points'] += 1
            standings[group][team1]['d'] += 1
            standings[group][team2]['d'] += 1
            logger.debug(f"Match drawn. Updated standings: {team1} points: {standings[group][team1]['points']}, {team2} points: {standings[group][team2]['points']}")

        standings[group][team1]['gf'] += team1_score
        standings[group][team1]['ga'] += team2_score
        standings[group][team1]['gd'] += team1_score - team2_score
        standings[group][team1]['gp'] += 1

        standings[group][team2]['gf'] += team2_score
        standings[group][team2]['ga'] += team1_score
        standings[group][team2]['gd'] += team2_score - team1_score
        standings[group][team2]['gp'] += 1

    logger.debug("Completed processing matches. Calculating standings dataframe.")

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
    logger.debug("Sorted standings dataframe by group, points, goal difference, and goals for.")

    third_place_teams = standings_df.groupby('group').nth(2)
    third_place_teams = third_place_teams.sort_values(by=['points', 'gd', 'gf'], ascending=[False, False, False]).head(4)
    logger.debug("Calculated third place teams.")

    standings_df.loc[standings_df.groupby('group').head(2).index, 'qualified'] = 'qualified'
    standings_df.loc[third_place_teams.index, 'qualified'] = 'best-third'
    logger.debug("Updated qualification status for top two teams and best third-place teams.")

    logger.debug("Completed compute_standings function.")
    return standings_df
