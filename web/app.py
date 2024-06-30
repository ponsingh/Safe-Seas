from flask import Flask, render_template,request, jsonify
import os
import pandas as pd

app = Flask(__name__)

# Define the routes and their respective handlers

# Load the data
# Debug: Print the current working directory
print("Current working directory:", os.getcwd())

# Load the data
try:
    routes_df = pd.read_csv('routes.csv')
    incidents_df = pd.read_csv('incidents.csv')
except FileNotFoundError as e:
    print(f"File not found: {e.filename}")
    raise

@app.route('/')
def index():
    if routes_df.empty:
        routes = []
        print("Routes dataframe is empty")
    else:
        routes = routes_df.to_dict(orient='records')    
    return render_template('index.html',routes=routes)

@app.route('/dashboard')
def dashboard():
    routes = routes_df.to_dict(orient='records')
    return render_template('dashboard.html')


@app.route('/incidents/<route_id>')
def incidents(route_id):
    try:
        route_incidents = incidents_df[incidents_df['RouteID'] == str(route_id)]
        incidents = route_incidents.to_dict(orient='records')
        return render_template('incidents.html', incidents=incidents)
    except e:
        print(f"File not found: {e}")
        raise

@app.route('/risk_calculator')
def risk_calculator():
    return render_template('risk_calculator.html')

# Run the application
if __name__ == "__main__":
    app.run(debug=True)
