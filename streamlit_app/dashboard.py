import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

API_URL = "http://127.0.0.1:5000"

# Step 1: Get available trucks
vin_list = requests.get(f"{API_URL}/trucks").json()
selected_vin = st.selectbox("Select Truck VIN", vin_list)

# Optional: Date-time range input
st.markdown("### Optional Time Filter")
start_time = st.text_input("Start Time (YYYY-MM-DDTHH:MM:SS)", "2024-01-01T08:00:00")
end_time = st.text_input("End Time (YYYY-MM-DDTHH:MM:SS)", "2024-01-01T10:00:00")

# Step 2: Analyze + Display
if st.button("🔍 Run Anomaly Analysis + Show Data"):
    # 1. Trigger analysis and fetch anomalies directly
    anom_resp = requests.post(f"{API_URL}/analyze/{selected_vin}/anomalies")
    if anom_resp.status_code != 200:
        st.error("Anomaly analysis failed.")
        df_anom = pd.DataFrame()
    else:
        df_anom = pd.DataFrame(anom_resp.json())
        st.success(f"Anomaly analysis complete. {len(df_anom)} anomalies detected.")

    if not df_anom.empty:
        # Apply client-side time filtering
        df_anom['timestamp'] = pd.to_datetime(df_anom['timestamp'])
        df_anom = df_anom[
            (df_anom['timestamp'] >= pd.to_datetime(start_time)) &
            (df_anom['timestamp'] <= pd.to_datetime(end_time))
        ]

        st.subheader(f"📊 {len(df_anom)} Anomalies in Time Range")
        st.dataframe(df_anom)

        # Filter anomalies with valid GPS
        # Filter anomalies with valid GPS
    df_map = df_anom[['latitude', 'longitude']].dropna()
    lat_center = (df_map['latitude'].min() + df_map['latitude'].max()) / 2
    lon_center = (df_map['longitude'].min() + df_map['longitude'].max()) / 2

    if not df_map.empty:
        st.subheader("📍 Anomaly Map")

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=lat_center,   # Neutral value or fallback
                longitude=lon_center,
                zoom=1,       # Zoomed out to show all points
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


        # Download option
        st.download_button("📥 Download Anomalies CSV", df_anom.to_csv(index=False), "anomalies.csv")

    else:
        st.warning("No anomalies found for this VIN or time range.")


