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

@app.route('/import_excel', methods=['POST'])
def import_excel():
    try:
        # Check if file part is present in the request
        if 'excel_file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        
        excel_file = request.files['excel_file']
        
        # Check if no file is selected
        if excel_file.filename == '':
            return jsonify({'error': 'No file selected for uploading'}), 400
        
        # Validate file extension
        if excel_file and allowed_file(excel_file.filename):
            try:
                # Load Excel file
                routes_df = pd.read_excel(excel_file, sheet_name='Routes')
                incidents_df = pd.read_excel(excel_file, sheet_name='Incidents')
                
                # Convert DataFrames to dictionaries
                routes_data = routes_df.to_dict(orient='records')
                incidents_data = incidents_df.to_dict(orient='records')
                
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



# Run the application
if __name__ == "__main__":
    app.run(debug=True)
