from flask import Flask, render_template
import os

app = Flask(__name__)

# Define the routes and their respective handlers

@app.route('/')
def index():
    return '<head>Test</head>'
    #return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/risk_calculator')
def risk_calculator():
    return render_template('risk_calculator.html')

# Run the application
if __name__ == "__main__":
    app.run(debug=True)
