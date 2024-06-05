import pandas as pd
from datetime import datetime, timedelta

def transform_data(data, teams, look_back_months):
    current_date = datetime.now()
    cutoff_date = current_date - timedelta(days=look_back_months * 30)
    data['date'] = pd.to_datetime(data['date'])
    data = data[data.date >= cutoff_date]

    data = data[data.away_team.isin(teams) | data.home_team.isin(teams)]
    
    return data
