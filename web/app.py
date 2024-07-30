from flask import Flask, render_template,request, jsonify,g
import os
import pandas as pd
import pickle
from datetime import datetime, timedelta
import requests
import re

#Constructor
app = Flask(__name__)



global routes_data, incidents_data

# Define the routes and their respective handlers

# Load the data
# Debug: Print the current working directory
print("Current working directory:", os.getcwd())

# Load the risk_model
with open('risk_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Load the risk_randomforest_model
with open('risk_randomforest_model.pkl', 'rb') as f:
    model_rf = pickle.load(f)


# Load the data
try:
    routes_df = pd.read_csv('Routes.csv')
    incidents_df = pd.read_csv('Incidents.csv')
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

@app.route('/incidents/<route_id>')
def incidents(route_id):
    try:
        route_incidents = incidents_df[incidents_df['Route_Id'] == str(route_id)]
        incidents = route_incidents.to_dict(orient='records')
        return render_template('incidents.html', incidents=incidents)
    except e:
        print(f"File not found: {e}")
        raise

@app.route('/risk_calculator')
def risk_calculator():
    return render_template('risk_calculator.html')

@app.route('/import_excel', methods=['POST'])
def import_excel():
    try:
        # Check if file part is present in the request
        print("Import file process started 1...")
        if 'excel_file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        
        excel_file = request.files['excel_file']
        is_fetch_future= request.form.get('checkbox_state')
        # Check if no file is selected
        if excel_file.filename == '':
            return jsonify({'error': 'No file selected for uploading'}), 400

        print("Import file process started 2...")

        # Validate file extension
        if excel_file and allowed_file(excel_file.filename):
            try:
                # Load Excel file
                xls = pd.ExcelFile(excel_file)
                sheet_names = xls.sheet_names
                print(f"Available sheet names: {sheet_names}")

                # Ensure 'Routes' sheet is present
                if 'Routes' not in sheet_names:
                    return jsonify({'error': f"'Routes' sheet not found. Available sheets: {sheet_names}"}), 400

                print("Import file process started 3...")
                global routes_data, incidents_data
                routes_df = pd.read_excel(excel_file, sheet_name='Routes')
                print("Import file process started 4...")
                incidents_df = pd.read_excel(excel_file, sheet_name='Incidents')
                if is_fetch_future == "true":
                    updated_incidents_df = process_futures_weather_incidents(incidents_df, routes_df)
                else:
                    updated_incidents_df=incidents_df

                routes_data=routes_df
                incidents_data=updated_incidents_df
                # Convert DataFrames to dictionaries
                updated_routes_data_dic = routes_df.to_dict(orient='records')
                updated_incidents_df_data = updated_incidents_df.to_dict(orient='records')
                
                print("Import file process completed...")

                # Return JSON response with routes and incidents data
                return jsonify({'routes': updated_routes_data_dic, 'incidents': updated_incidents_df_data})
            
            except Exception as e:
                return jsonify({'error': f'Error processing Excel file: {str(e)}'}), 500
        
        else:
            return jsonify({'error': 'Allowed file types are xls, xlsx'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500
    
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_futures_weather_incidents(incidents_df, routes_df):
    try:
        get_string = str(routes_df.iloc[0]['Stop_Points'])
        coordinates = re.findall(r"\[([\d.]+)\s*,\s*([\d.]+)\]", get_string)
        latitude_longitude_pairs = [(float(lat), float(lon)) for lat, lon in coordinates]
        
        url = "https://api.open-meteo.com/v1/forecast"
        for lat, lon in latitude_longitude_pairs:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': "pressure_msl",
                'daily': ["uv_index_max", "precipitation_sum", "rain_sum", "showers_sum", "snowfall_sum", "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant", "shortwave_radiation_sum"],
                'forecast_days': 16
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            df = pd.DataFrame(data['daily'])
            
            df['Incident_Id'] = range(len(incidents_df) + 1, len(incidents_df) + len(df) + 1)
            df['Route_Id'] = routes_df.iloc[0]['Route_Id']
            df['Incident_Type'] = df.apply(determine_incident_type, axis=1)
            df['Severity'] = df.apply(determine_severity, axis=1)
            #df['Incident_Date'] = df['time']
            df['Incident_Date'] = pd.to_datetime(df['time'])
            df['Description'] = df.apply(generate_description, axis=1)
            
            new_df = df[['Incident_Id', 'Route_Id', 'Incident_Type', 'Severity', 'Incident_Date', 'Description']]
            incidents_df = pd.concat([incidents_df, new_df], ignore_index=True)
        
        return incidents_df
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return incidents_df

# Function definitions
def determine_severity(row):
    if row['precipitation_sum'] > 50 or row['wind_gusts_10m_max'] > 40 or row['precipitation_probability_max'] > 90:
        return 'High'
    elif row['precipitation_sum'] > 20 or row['wind_gusts_10m_max'] > 30 or row['precipitation_probability_max'] > 70:
        return 'Medium'
    else:
        return 'Low'

def generate_description(row):
    description = []
    if row['precipitation_sum'] > 20:
        description.append('Heavy precipitation')
    if row['rain_sum'] > 10:
        description.append('Significant rainfall')
    if row['showers_sum'] > 10:
        description.append('Frequent showers')
    if row['precipitation_probability_max'] > 80:
        description.append('High probability of precipitation')
    if row['wind_speed_10m_max'] > 15:
        description.append('Strong winds')
    if row['wind_gusts_10m_max'] > 30:
        description.append('Strong wind gusts')
    if row['shortwave_radiation_sum'] > 10:
        description.append('High solar radiation')
    if row['uv_index_max'] > 5:
        description.append('High UV index')
    return ', '.join(description) if description else 'Normal weather conditions'

def determine_incident_type(row):
    incident_types = []
    if row['precipitation_sum'] > 50:
        incident_types.append('Heavy Rainfall')
    elif row['precipitation_sum'] > 20:
        incident_types.append('Moderate Rainfall')
    if row['wind_gusts_10m_max'] > 40:
        incident_types.append('Severe Winds')
    elif row['wind_gusts_10m_max'] > 30:
        incident_types.append('Strong Winds')
    if row['uv_index_max'] > 5:
        incident_types.append('High UV')
    if row['shortwave_radiation_sum'] > 10:
        incident_types.append('High Solar Radiation')
    return ', '.join(incident_types) if incident_types else 'No Significant Incident'

# Function to get the date 5 months ago
def date_n_months_ago(current_date, n):
    return current_date - timedelta(days=n*30)  # Approximate 5 months as 150 days

@app.route('/calculate_risk_score', methods=['POST'])
def calculate_risk_score():
    try:
        global routes_data, incidents_data
        c=len(routes_data)
        print("Calculating risk score...")
        # Current date
        current_date = datetime.now()
        five_months_ago = date_n_months_ago(current_date, 5)
        # Adding columns to routes dataframe




        df_incidents = pd.DataFrame(incidents_data)
        df_routes = pd.DataFrame(routes_data)
        df_routes['Total_Incidents_Count'] = 0
        df_routes['high_incidents'] = 0
        df_routes['high_last5Month_incidents'] = 0
        df_routes['medium_incidents'] = 0
        df_routes['medium_last5Month_incidents'] = 0
        df_routes['low_incidents'] = 0
        df_routes['low_last5Month_incidents'] = 0

        for index,row in df_routes.iterrows():
            #total incidents and count
            route_incidents=df_incidents[df_incidents['Route_Id']==row['Route_Id']]   
            incidents_count=route_incidents.shape[0]
            df_routes.loc[index, 'Total_Incidents_Count']=incidents_count
            
            #High incidents and count
            high_incidents = route_incidents[route_incidents['Severity'] == 'High']
            high_count=high_incidents.shape[0]
            high_last5Month_count=high_incidents[high_incidents['Incident_Date']>five_months_ago].shape[0]

            df_routes.loc[index, 'high_incidents']=(high_count-high_last5Month_count)
            df_routes.loc[index, 'high_last5Month_incidents']=high_last5Month_count

            
            
            #Medium incidents and count
            medium_incidents = route_incidents[route_incidents['Severity'] == 'Medium']
            medium_count=medium_incidents.shape[0]
            medium_last5Month_count=medium_incidents[medium_incidents['Incident_Date']>five_months_ago].shape[0]
            df_routes.loc[index, 'medium_incidents'] = (medium_count-medium_last5Month_count)
            df_routes.loc[index, 'medium_last5Month_incidents'] = medium_last5Month_count
            
                #Medium incidents and count
            low_incidents = route_incidents[route_incidents['Severity'] == 'Low']
            low_count=low_incidents.shape[0]
            low_last5Month_count=low_incidents[low_incidents['Incident_Date']>five_months_ago].shape[0]
            df_routes.loc[index, 'low_incidents'] = (low_count-low_last5Month_count)
            df_routes.loc[index, 'low_last5Month_incidents'] =low_last5Month_count


        # Load your data from a source or import it dynamically if needed
        # Example: Read from a CSV file or database
        # Here, we're using static data for demonstration         
         # Convert data into DataFrame
        # Create a DataFrame with new data points to predict

        columns_to_keep = ['Distance', 
                           'Average_Transit_Days', 
                           'No_Of_Travels',
                           'Total_Incidents_Count',
                           'high_incidents',
                           'high_last5Month_incidents',
                           'medium_incidents',
                           'medium_last5Month_incidents',
                           'low_incidents',
                           'low_last5Month_incidents']
        
        new_data = df_routes[columns_to_keep].copy()
    #     new_data = pd.DataFrame({
    # 'Distance': [500, 850, 200],
    # 'Average_Transit_Days': [13, 25, 12],
    # 'No_Of_Travels': [900, 2008, 3330],
    # 'Total_Incidents_Count': [600, 150, 300],
    # 'high_incidents': [400, 10, 45],
    # 'high_last5Month_incidents': [50, 0, 5],
    # 'medium_incidents': [50, 100, 100],
    # 'medium_last5Month_incidents': [0, 2, 50],
    # 'low_incidents': [50, 28, 100],
    # 'low_last5Month_incidents': [50, 10, 0]
    #     })
    
            # Make prediction
        prediction = model_rf.predict(new_data)
        
        risk_value=prediction[0]
        if risk_value>100:
            risk_value=100
        
        if risk_value<7:
            risk_value=7
        
        #return {'Risk_Score': risk_value}

        route_color="blue"
        if risk_value>60:
            route_color="red"
        elif risk_value>20:
            route_color="yellow"
        else:
            route_color="green"
    
        return jsonify({'Risk_Score': risk_value,
                        "route_color":route_color})

    except Exception as e:
        return jsonify({'Risk_Score': 0,
                        "route_color":"blue"})


# Run the application
if __name__ == "__main__":
    app.run(debug=True)
