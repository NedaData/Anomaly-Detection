import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import os

API_URL = os.getenv("API_URL", "http://localhost:5000")

st.title("🚛 Telematics Anomaly Dashboard")

# === STEP 0: Upload CSV File ===
st.header("📤 Upload Telematics Data")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    files = {'file': uploaded_file}
    upload_response = requests.post(f"{API_URL}/upload", files=files)
    if upload_response.status_code == 200:
        st.success("✅ File uploaded successfully.")
    else:
        st.error("❌ Upload failed. Make sure the Flask server is running.")

# === STEP 1: Select Truck ===
st.header("🚛 Select Truck for Analysis")
try:
    vin_list = requests.get(f"{API_URL}/trucks").json()
    selected_vin = st.selectbox("Select Truck VIN", vin_list)
except Exception as e:
    st.error(f"⚠️ Failed to fetch truck list: {e}")
    st.stop()

# === Optional Date Filter ===
st.markdown("### ⏱️ Optional Time Filter")
start_time = st.text_input("Start Time (YYYY-MM-DDTHH:MM:SS)", "2024-01-01T08:00:00")
end_time = st.text_input("End Time (YYYY-MM-DDTHH:MM:SS)", "2024-01-01T10:00:00")

# === STEP 2: Analyze and Visualize ===
if st.button("🔍 Run Anomaly Analysis + Show Data"):
    try:
        # 1. Trigger analysis
        anom_resp = requests.get(f"{API_URL}/analyze/{selected_vin}/anomalies")
        if anom_resp.status_code != 200:
            st.error(f"Anomaly analysis failed: {anom_resp.status_code} - {anom_resp.text}")
            st.stop()
        else:

        # 2. Display anomalies
            df_anom = pd.DataFrame(anom_resp.json())
            st.success(f"Anomaly analysis complete. {len(df_anom)} anomalies detected.")

        if not df_anom.empty:
            # Convert timestamps and filter
            df_anom['timestamp'] = pd.to_datetime(df_anom['timestamp'])
            df_anom = df_anom[
                (df_anom['timestamp'] >= pd.to_datetime(start_time)) &
                (df_anom['timestamp'] <= pd.to_datetime(end_time))
            ]

            st.subheader(f"📊 {len(df_anom)} Anomalies in Time Range")
            st.dataframe(df_anom)

            # Extract map data
            df_map = df_anom[['latitude', 'longitude']].dropna()
            if not df_map.empty:
                st.subheader("📍 Anomaly Map")
                lat_center = (df_map['latitude'].min() + df_map['latitude'].max()) / 2
                lon_center = (df_map['longitude'].min() + df_map['longitude'].max()) / 2

                st.pydeck_chart(pdk.Deck(
                    initial_view_state=pdk.ViewState(
                        latitude=lat_center,
                        longitude=lon_center,
                        zoom=8,
                        pitch=0,
                    ),
                    layers=[
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=df_map,
                            get_position='[longitude, latitude]',
                            get_color='[255, 0, 0, 160]',
                            get_radius=100,
                            pickable=True,
                        )
                    ],
                ))

            # Download anomalies CSV
            st.download_button("📥 Download Anomalies CSV", df_anom.to_csv(index=False), "anomalies.csv")

        else:
            st.warning("No anomalies found for this VIN or time range.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
