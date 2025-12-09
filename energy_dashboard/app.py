from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
import datetime
import threading
import time
import os

app = Flask(__name__)

# -------------------------------
# Simulated Live Data
# -------------------------------
df = pd.DataFrame(columns=["timestamp", "consumption"])
ANOMALY_THRESHOLD = 180  # define anomaly threshold
ANOMALY_LOG_FILE = "anomalies.log"

# Ensure log file exists
if not os.path.exists(ANOMALY_LOG_FILE):
    open(ANOMALY_LOG_FILE, "w").close()

def log_anomaly(row):
    """Append anomaly to text file"""
    with open(ANOMALY_LOG_FILE, "a") as f:
        f.write(f"{row['timestamp']} - Anomaly detected: {row['consumption']}\n")

def generate_data():
    global df
    while True:
        timestamp = datetime.datetime.now()
        consumption = np.random.randint(50, 200)
        new_row = {"timestamp": timestamp, "consumption": consumption}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Check for anomaly
        if consumption > ANOMALY_THRESHOLD:
            log_anomaly(new_row)

        time.sleep(2)  # new data every 2 seconds

threading.Thread(target=generate_data, daemon=True).start()

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/data")
def get_data():
    global df
    last_data = df.tail(500).copy()  # keep last 500 records
    last_data["timestamp"] = last_data["timestamp"].astype(str)
    return jsonify(last_data.to_dict(orient="records"))

@app.route("/anomalies")
def get_anomalies():
    global df
    anomalies = df[df['consumption'] > ANOMALY_THRESHOLD].tail(50).copy()
    anomalies["timestamp"] = anomalies["timestamp"].astype(str)
    return jsonify(anomalies.to_dict(orient="records"))

# -------------------------------
# Run Flask
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
