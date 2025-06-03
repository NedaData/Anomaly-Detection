from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import os

app = Flask(__name__)

DATA = pd.DataFrame()
ANOMALIES = pd.DataFrame()

REQUIRED_COLUMNS = ['vin', 'timestamp', 'latitude', 'longitude', 'hour', 'day_of_week', 'dist_m', 'truck_type_code']

@app.route("/upload", methods=["POST"])
def upload():
    global DATA
    file = request.files['file']
    df = pd.read_csv(file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    DATA = pd.concat([DATA, df], ignore_index=True)
    return jsonify({"message": "Upload successful", "rows": len(df)})

@app.route("/trucks", methods=["GET"])
def trucks():
    return jsonify(DATA['vin'].dropna().unique().tolist())

@app.route("/truck/<vin>/behavior", methods=["GET"])
def behavior(vin):
    df = DATA[DATA['vin'] == vin].copy()
    return jsonify(df.to_dict(orient="records"))


@app.route("/analyze/<vin>/anomalies", methods=["GET"])
def analyze_and_return_anomalies(vin):
    df = DATA[DATA['vin'] == vin].copy()
    df = df.dropna()
    if df.empty:
        return jsonify({"message": "No data found for this VIN."}), 404

    features = ['latitude', 'longitude', 'hour', 'day_of_week', 'dist_m', 'truck_type_code']
    model = IsolationForest(contamination=0.05, random_state=42)
    df['is_anomaly'] = model.fit_predict(df[features])
    df['is_anomaly'] = (df['is_anomaly'] == -1).astype(int)

    anomalies_only = df[df['is_anomaly'] == 1].copy()
    return jsonify(anomalies_only.to_dict(orient="records"))


if __name__ == '__main__':
    app.run(debug=True)
