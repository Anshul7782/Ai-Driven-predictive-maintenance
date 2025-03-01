from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import joblib
import mysql.connector
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', prediction_result=None, warning_message=None)

def validate_input(input_data):
    warnings = []
    feature_ranges = {
        'temperature': (25, 100),   
        'vibration': (0.18, 0.9),   
        'fuel_level': (15, 100),    
        'speed': (0, 100),          
        'engine_rpm': (700, 3000)   
    }

    for feature, value in zip(feature_ranges.keys(), input_data[0]):
        min_val, max_val = feature_ranges[feature]
        if value < min_val or value > max_val:
            warnings.append(f"Warning: {feature} value {value} is out of expected range ({min_val}, {max_val}) Maintenace Required")
    return warnings

@app.route('/predict', methods=['POST'])
def predict():
    try:
        temperature = float(request.form['temperature'])
        vibration = float(request.form['vibration'])
        fuel_level = float(request.form['fuel_level'])
        speed = float(request.form['speed'])
        engine_rpm = float(request.form['engine_rpm'])

        input_data = np.array([temperature, vibration, fuel_level, speed, engine_rpm]).reshape(1, -1)

        warnings = validate_input(input_data)
        warning_message = "<br>".join(warnings) if warnings else ""

        prediction = model.predict(input_data)

        if prediction == 1:
            result = "Warning: Predicted failure, maintenance required!"
            result_class = "failure"
        else:
            result = "No failure predicted, all systems normal."
            result_class = "no-failure"

        timestamp = datetime.now()
        connection = mysql.connector.connect(
            host='localhost',
            database='predictive_maintenance',
            user='root',
            password='Write your sql password'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO predictions (temperature, vibration, fuel_level, speed, engine_rpm, prediction, message) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (temperature, vibration, fuel_level, speed, engine_rpm, result, warning_message)
            )
            connection.commit()
            connection.close()

        return render_template('index.html', prediction_result=f"{result}<br>{warning_message}",
                               temperature=temperature, vibration=vibration,
                               fuel_level=fuel_level, speed=speed, engine_rpm=engine_rpm,
                               result_class=result_class)

    except Exception as e:
        return render_template('index.html', prediction_result=f"Error: {str(e)}")

@app.route('/history')
def history():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='predictive_maintenance',
            user='root',
            password='Write your sql password'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM predictions ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            connection.close()
            return render_template('history.html', predictions=rows)

    except mysql.connector.Error as e:
        return f"Error: {e}"

@app.route('/delete_all', methods=['POST'])
def delete_all_records():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='predictive_maintenance',
            user='root',
            password='Write your sql password'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("DELETE FROM predictions")
            connection.commit()
            connection.close()

        return redirect(url_for('history'))

    except mysql.connector.Error as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True)
