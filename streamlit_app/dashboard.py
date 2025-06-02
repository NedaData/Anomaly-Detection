import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

#API_URL = "http://127.0.0.1:5000"
import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
st.set_page_config(layout="wide", page_title="Telematics Dashboard")
st.title("📊 Truck Telematics Analyzer")

# === Session State Defaults ===
if "uploaded" not in st.session_state:
    st.session_state.uploaded = False
if "df_result" not in st.session_state:
    st.session_state.df_result = None

# === Manual Reset Button ===
if st.button("Reset Session"):
    st.session_state.uploaded = False
    st.session_state.df_result = None
    st.rerun()

# === File Upload ===
if not st.session_state.uploaded:
    uploaded_file = st.file_uploader("Upload Telematics CSV", type="csv")
    if uploaded_file:
        try:
            res = requests.post(f"{API_URL}/upload", files={"file": uploaded_file})
            rows_uploaded = res.json().get("rows", 0)
            st.success(f"Upload successful: {rows_uploaded} rows")
            st.session_state.uploaded = True
            st.rerun() 
        except Exception as e:
            st.error(f"Upload failed: {e}")
            st.stop()

# === Get Truck List ===
try:
    truck_list = requests.get(f"{API_URL}/trucks").json()
except:
    st.error("Could not connect to Flask API.")
    st.stop()

if not truck_list:
    st.warning("No trucks found in uploaded data.")
    st.stop()

# === VIN & Filter Inputs ===
selected_vin = st.selectbox("Select Truck VIN", truck_list)
col1, col2 = st.columns(2)
with col1:
    start_time = st.text_input("Start Time (e.g. 2024-01-01T08:00:00)", "")
with col2:
    end_time = st.text_input("End Time (e.g. 2024-01-01T10:00:00)", "")
anomalies_only = st.checkbox("Show only anomalies", value=False)


# === Analyze Button ===
if st.button("Analyze Route"):
    try:
        # Trigger backend anomaly detection
        requests.post(f"{API_URL}/analyze", json={"vin": selected_vin, "start": start_time, "end": end_time})
    except:
        st.warning(" Could not trigger analysis. It might have already run.")

    try:
        # Get filtered results
        params = {"vin": selected_vin, "start": start_time, "end": end_time}
        if anomalies_only:
            params["anomaly_type"] = "iforest"

        response = requests.get(f"{API_URL}/data", params=params)
        df = pd.DataFrame(response.json())

        if df.empty:
            st.warning("No data found for this filter.")
        else:
            st.success(f"Retrieved {len(df)} records.")
            st.session_state.df_result = df  # Store in session state
    except Exception as e:
        st.error(f"Error retrieving data: {e}")

# === Display Saved Results ===
if st.session_state.df_result is not None:
    df = st.session_state.df_result

    st.dataframe(df)

    st.subheader("Route Map")
    m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=12)
    for _, row in df.iterrows():
        color = "red" if row.get("iforest_anomaly", 0) == 1 else "blue"
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.7
        ).add_to(m)
    st_folium(m, height=500)

    st.download_button("Download Data", df.to_csv(index=False), file_name=f"{selected_vin}_data.csv")
