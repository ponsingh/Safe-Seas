from flask import Flask, render_template,request, jsonify,g
import os
import pandas as pd

#Constructor
app = Flask(__name__)

# Define the routes and their respective handlers

# Load the data
# Debug: Print the current working directory
print("Current working directory:", os.getcwd())

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
                g.routes_data = routes_df.to_dict(orient='records')
                g.incidents_data = incidents_df.to_dict(orient='records')
                
                print("Import file process completed...")

                # Return JSON response with routes and incidents data
                return jsonify({'routes': g.routes_data, 'incidents': g.incidents_data})
            
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
        print("Calculating risk score...")
        # Load your data from a source or import it dynamically if needed
        # Example: Read from a CSV file or database
        # Here, we're using static data for demonstration
        
        return {'Risk_Score': 100}

        routes_data = [
            {"route_id": 1, "load_port": "London", "discharge_port": "New York", "coordinates": [[51.5, -0.1], [40.7, -74.0]]},
            {"route_id": 2, "load_port": "Tokyo", "discharge_port": "San Francisco", "coordinates": [[35.6, 139.7], [37.8, -122.4]]}
        ]
        incidents_data = [
            {"incident_id": 1, "route_id": 1, "description": "Storm", "Risk_Score": 70},
            {"incident_id": 2, "route_id": 2, "description": "Piracy", "Risk_Score": 90}
        ]

        # Convert data to DataFrame if needed
        routes_df = pd.DataFrame(routes_data)
        incidents_df = pd.DataFrame(incidents_data)

        # Feature Engineering: Combine routes and incidents data if needed
        # Example: Join on route_id and create features for the model
        combined_df = pd.merge(routes_df, incidents_df, on='route_id')

        # Extract features for prediction (this depends on your model's requirements)
        # For simplicity, we are just using Risk_Score from incidents in this example
        X = combined_df[['Risk_Score']]  # Replace with actual feature columns used in your model

        # Predict risk score using the model
        predicted_risk_scores =45 #model.predict(X)

        # Example of how you might calculate a summary risk score
        summary_risk_score = np.mean(predicted_risk_scores)

        return jsonify({'Risk_Score': summary_risk_score})

    except Exception as e:
        return {'Risk_Score': 20}


# Run the application
if __name__ == "__main__":
    app.run(debug=True)
