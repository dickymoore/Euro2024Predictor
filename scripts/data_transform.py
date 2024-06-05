import pandas as pd
from datetime import datetime, timedelta

def transform_data(data, teams, look_back_days):
    current_date = datetime.now()
    cutoff_date = current_date - timedelta(days=look_back_days)
    
    # Filter by date
    data['date'] = pd.to_datetime(data['date'])
    data = data[data['date'] >= cutoff_date]
    
    # Filter by teams
    data = data[data['team'].isin(teams)]
    
    return data
