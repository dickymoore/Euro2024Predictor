from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Function to load data and prepare it for the template
def load_prediction_data():
    # Load your data (replace with actual data loading logic)
    csv_path = 'data/results.csv'
    data = pd.read_csv(csv_path)
    
    # Process data into the required format for the template
    # Here you should transform your data to fit the structure of the wall chart
    groups = {}
    for group in data['group'].unique():
        groups[group] = data[data['group'] == group].to_dict(orient='records')
    
    return groups

@app.route('/')
def index():
    # Load and process the prediction data
    prediction_data = load_prediction_data()
    return render_template('index.html', prediction_data=prediction_data)

if __name__ == '__main__':
    app.run(debug=True)
