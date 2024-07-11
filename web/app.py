from flask import Flask, render_template,request, jsonify,g
import os
import pandas as pd
import pickle

#Constructor
app = Flask(__name__)



global routes_data, incidents_data

# Define the routes and their respective handlers

# Load the data
# Debug: Print the current working directory
print("Current working directory:", os.getcwd())

# Load the model
with open('risk_model.pkl', 'rb') as f:
    model = pickle.load(f)

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
                routes_df = pd.read_excel(excel_file, sheet_name='Routes')
                print("Import file process started 4...")
                incidents_df = pd.read_excel(excel_file, sheet_name='Incidents')
                
                # Convert DataFrames to dictionaries
                global routes_data, incidents_data
                routes_data = routes_df.to_dict(orient='records')
                incidents_data = incidents_df.to_dict(orient='records')
                
                print("Import file process completed...")

                # Return JSON response with routes and incidents data
                return jsonify({'routes': routes_data, 'incidents': incidents_data})
            
            except Exception as e:
                return jsonify({'error': f'Error processing Excel file: {str(e)}'}), 500
        
        else:
            return jsonify({'error': 'Allowed file types are xls, xlsx'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/calculate_risk_score', methods=['POST'])
def calculate_risk_score():
    try:
        global routes_data, incidents_data
        c=len(routes_data)
        print("Calculating risk score...")
        # Load your data from a source or import it dynamically if needed
        # Example: Read from a CSV file or database
        # Here, we're using static data for demonstration         
         # Convert data into DataFrame
        # Create a DataFrame with new data points to predict
        new_data = pd.DataFrame({
    'Distance': [500, 850, 200],
    'Average_Transit_Days': [13, 25, 12],
    'No_Of_Travels': [9000, 2008, 3330],
    'Total_Incidents_Count': [600, 150, 300],
    'high_incidents': [400, 10, 45],
    'high_last5Month_incidents': [50, 0, 5],
    'medium_incidents': [50, 100, 100],
    'medium_last5Month_incidents': [0, 2, 50],
    'low_incidents': [50, 28, 100],
    'low_last5Month_incidents': [50, 10, 0]
        })
    
            # Make prediction
        prediction = model.predict(new_data)
        
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
