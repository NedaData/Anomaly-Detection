import os
from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
from threading import Thread
import requests

app = Flask(__name__)

# In-memory storage
DATA = pd.DataFrame()
ANOMALIES = pd.DataFrame()
WEBHOOKS = {}

# === Config ===
REQUIRED_COLUMNS = ['vin', 'timestamp', 'latitude', 'longitude', 'hour', 'day_of_week', 'dist_m', 'truck_type_code']

# === Utility ===
def notify_webhooks(vin, anomaly_record):
    if vin in WEBHOOKS:
        for url in WEBHOOKS[vin]:
            def send():
                try:
                    requests.post(url, json=anomaly_record)
                except Exception as e:
                    print(f"Webhook failed: {e}")
            Thread(target=send).start()

# === Routes ===
@app.route("/upload", methods=["POST"])
def upload():
    global DATA
    if "file" not in request.files:
        return jsonify({"error": "No file part."}), 400

    file = request.files["file"]
    df = pd.read_csv(file)

    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        return jsonify({"error": f"Missing columns: {REQUIRED_COLUMNS}"}), 400

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', infer_datetime_format=True)
    DATA = pd.concat([DATA, df], ignore_index=True)
    return jsonify({"message": "Upload successful.", "rows": len(df)})

@app.route("/trucks", methods=["GET"])
def get_trucks():
    vins = DATA['vin'].dropna().unique().tolist()
    return jsonify(sorted(vins))

@app.route("/truck/<vin>/behavior", methods=["GET"])
def truck_behavior(vin):
    df = DATA[DATA['vin'] == vin]
    if df.empty:
        return jsonify({"error": "VIN not found."}), 404

    start = request.args.get("start")
    end = request.args.get("end")

    if start:
        df = df[df['timestamp'] >= pd.to_datetime(start)]
    if end:
        df = df[df['timestamp'] <= pd.to_datetime(end)]

    summary = {
        "vin": vin,
        "total_distance": df['dist_m'].sum(),
        "average_hour": df['hour'].mean(),
        "zone_visits": list(df[['latitude', 'longitude']].drop_duplicates().values.tolist())
    }
    return jsonify(summary)

@app.route("/truck/<vin>/anomalies", methods=["GET"])
def get_anomalies(vin):
    df = ANOMALIES[ANOMALIES['vin'] == vin]
    return jsonify(df.to_dict(orient="records"))


@app.route("/analyze", methods=["POST"])
def analyze():
    global ANOMALIES
    try:
        data = request.get_json(force=True) or {}
    except Exception as e:
        return jsonify({"error": f"Invalid JSON payload: {str(e)}"}), 400

    vin = data.get("vin")
    start = data.get("start")
    end = data.get("end")

    vins = [vin] if vin else DATA['vin'].dropna().unique().tolist()

    if not vins:
        return jsonify({"error": "No VINs found in data."}), 400

    total_anomalies = 0
    for v in vins:
        df = DATA[DATA['vin'] == v]
        if df.empty:
            continue

        if start:
            df = df[df['timestamp'] >= pd.to_datetime(start)]
        if end:
            df = df[df['timestamp'] <= pd.to_datetime(end)]
        


        df = df.dropna(subset=['latitude', 'longitude', 'hour', 'day_of_week', 'dist_m', 'truck_type_code']).reset_index(drop=True)
        if df.empty:
            continue

        X = df[['latitude', 'longitude', 'hour', 'day_of_week', 'dist_m', 'truck_type_code']]

        clf = IsolationForest(contamination=0.05, random_state=42)
        preds = clf.fit_predict(X)

        anomalies = df.copy()
        anomalies['anomaly_type'] = 'iforest'
        anomalies['is_anomaly'] = (preds == -1).astype(int)
        anomalies = anomalies[anomalies['is_anomaly'] == 1]

        total_anomalies += len(anomalies)
        ANOMALIES = pd.concat([ANOMALIES, anomalies], ignore_index=True)

        for _, row in anomalies.iterrows():
            notify_webhooks(v, row.to_dict())

    return jsonify({"anomalies_detected": total_anomalies})

# === ROUTE: Filtered data for a VIN (API-friendly for Streamlit) ===

@app.route("/data", methods=["GET"])
def get_data():
    vin = request.args.get("vin")
    start = request.args.get("start")
    end = request.args.get("end")
    anomaly_type = request.args.get("anomaly_type")

    df = ANOMALIES if anomaly_type == "iforest" else DATA

    df = df[df['vin'] == vin]
    if start:
        df = df[df['timestamp'] >= pd.to_datetime(start)]
    if end:
        df = df[df['timestamp'] <= pd.to_datetime(end)]

    return jsonify(df.to_dict(orient="records"))

@app.route("/webhooks/register", methods=["POST"])
def register_webhook():
    data = request.get_json()
    vin = data.get("vin")
    url = data.get("url")

    if vin not in WEBHOOKS:
        WEBHOOKS[vin] = []
    WEBHOOKS[vin].append(url)

    return jsonify({"message": f"Webhook registered for {vin}"})

@app.route("/", methods=["GET"])
def health():
    return jsonify({"message": "Truck Behavior API is running."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
