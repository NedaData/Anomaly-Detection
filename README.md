# Anomaly-Detection
System for Detecting Anomalous Truck Behavior Using Telematics Data

 # Key Features

Synthetic Data Generator: Simulates GPS routes with injected anomalies to validate models in a controlled setting.
Preprocessing & Feature Engineering: Cleans raw telematics data and extracts features like speed, heading, and positional deviation.
Anomaly Detection Engine: Uses various unsupervised learning models (e.g., Isolation Forest, Autoencoder, DBSCAN) to detect anomalous behavior.
API Backend: Flask-based REST API with routes for uploading data, retrieving truck behavior, and anomaly analysis.
Frontend Dashboard: Built with Streamlit for visualizing anomalies, filtering by VIN and time, and downloading results.
Deployment: Containerized using Docker and docker-compose for seamless service orchestration.

# Workflow diagram

Synthetic Data Model → 
Preprocessing & Feature Engineering →
Anomaly Detection Engine →
Flask API Backend →
Streamlit Dashboard →
Docker Deployment

# How to run:

Docker & docker-compose installed
Python 3.8+ (if running locally)


# Build and run
docker-compose up --build
git clone <your-repo-url>
cd telematics-anomaly-detector

# Build and run
docker-compose up --build

# Streamlit UI: http://localhost:8501
# Flask API: http://localhost:5000

 # Example Use Cases

Upload synthetic or real-world telematics CSV files
Select truck VIN and time range
Visualize anomalous routes and download results

# Tech Stack

Languages: Python
ML Libraries: Scikit-learn, TensorFlow (Autoencoder)
API: Flask
UI: Streamlit
Deployment: Docker
