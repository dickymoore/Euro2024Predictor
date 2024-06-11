import pandas as pd
from datetime import datetime, timedelta

def transform_data(data, teams, look_back_months):
    current_date = datetime.now()
    cutoff_date = current_date - timedelta(days=look_back_months * 30)
    
    # Convert date column to datetime
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    
    # Drop rows with invalid dates
    data = data.dropna(subset=['date'])
    
    # Filter data based on the cutoff date
    data = data[data.date >= cutoff_date]
    print(f"Filtered data by date. Rows remaining: {len(data)}")

    # Normalize team names
    data['home_team'] = data['home_team'].str.strip().str.upper()
    data['away_team'] = data['away_team'].str.strip().str.upper()
    teams = [team.strip().upper() for team in teams]

    # Filter data to include only specified teams
    data = data[data.away_team.isin(teams) | data.home_team.isin(teams)]
    print(f"Filtered data by teams. Rows remaining: {len(data)}")

    if data.empty:
        print("No data available after filtering by teams and date.")
        return pd.DataFrame(), pd.DataFrame()

    # Calculate average goals scored and conceded
    team_stats = data.groupby('home_team').agg(
        home_goals_scored=('home_score', 'mean'),
        home_goals_conceded=('away_score', 'mean')
    ).rename_axis('team').reset_index()
    print(f"Calculated home team stats. Sample: \n{team_stats.head()}")

    away_stats = data.groupby('away_team').agg(
        away_goals_scored=('away_score', 'mean'),
        away_goals_conceded=('home_score', 'mean')
    ).rename_axis('team').reset_index()
    print(f"Calculated away team stats. Sample: \n{away_stats.head()}")

    # Merge stats
    averages = pd.merge(team_stats, away_stats, on='team', how='outer').fillna(0)
    averages['average_goals_scored'] = (averages['home_goals_scored'] + averages['away_goals_scored']) / 2
    averages['average_goals_conceded'] = (averages['home_goals_conceded'] + averages['away_goals_conceded']) / 2
    averages.set_index('team', inplace=True)
    
    # Debugging: print the resulting averages DataFrame
    print(f"Averages DataFrame: \n{averages.head()}")

    return data, averages
