# pages_influx/1_Home.py

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from utils.data_processing_influx import (
    get_influxdb_client,
    update_df_from_db,
    calculate_uv_index,
    temperature_description,
    humidity_description,
    aqi_description,
    uv_description,
    ambient_light_description,
    pressure_description,
    calculate_dew_point,
    dew_point_description,
    calculate_heat_index,
    heat_index_description,
    calculate_iaq,
    get_theme_css
)
from utils.sidebar import render_sidebar
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide",
)

# Automatic refresh every 5 seconds
st_autorefresh(interval=5000, key="data_refresh")

# Render the sidebar
render_sidebar()

# Get the selected theme from session state
theme = st.session_state.get('theme', 'Dark')
css_styles = get_theme_css(theme)
st.markdown(css_styles, unsafe_allow_html=True)

# Title with custom styling
st.markdown("<h1 class='title'>Real-Time Weather Data Dashboard</h1>", unsafe_allow_html=True)

# Initialize session state variables if not already done
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.data_fetched = False
    st.session_state.last_fetch_time = None  # Will default to 1970-01-01 in the function

# Get InfluxDB client
client = get_influxdb_client()

# Update data
update_df_from_db(client)

# Function to get data from a specified time ago
def get_data_minutes_ago(df, minutes):
    if df.empty:
        return None
    target_time = df['Timestamp'].iloc[-1] - pd.Timedelta(minutes=minutes)
    data = df[df['Timestamp'] <= target_time]
    if not data.empty:
        return data.iloc[-1]
    else:
        return None

# Display latest data summary
if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df
    latest_data = df.iloc[-1]

    # Data from 30 minutes ago
    data_30_min_ago = get_data_minutes_ago(df, 30)

    # Calculate additional metrics
    uv_index = calculate_uv_index(latest_data['uv_data'])
    dew_point = calculate_dew_point(latest_data['temperature'], latest_data['humidity'])
    heat_index = calculate_heat_index(latest_data['temperature'], latest_data['humidity'])
    # Calculate IAQ
    iaq = calculate_iaq(latest_data['gas_resistance'], latest_data['humidity'])

    # Generate descriptions
    temp_desc = temperature_description(latest_data['temperature'])
    humidity_desc = humidity_description(latest_data['humidity'])
    pressure_desc = pressure_description(latest_data['pressure'])
    iaq_desc = aqi_description(iaq)
    uv_desc = uv_description(uv_index)
    light_desc = ambient_light_description(latest_data['ambient_light'])
    dew_point_desc = dew_point_description(dew_point)
    heat_index_desc = heat_index_description(heat_index)

    # Calculate delta values if data from 30 minutes ago is available
    if data_30_min_ago is not None:
        temp_delta = latest_data['temperature'] - data_30_min_ago['temperature']
        humidity_delta = latest_data['humidity'] - data_30_min_ago['humidity']
        pressure_delta = latest_data['pressure'] - data_30_min_ago['pressure']
        iaq_delta = iaq - calculate_iaq(data_30_min_ago['gas_resistance'], data_30_min_ago['humidity'])
        uv_index_delta = uv_index - calculate_uv_index(data_30_min_ago['uv_data'])
        light_delta = latest_data['ambient_light'] - data_30_min_ago['ambient_light']
        dew_point_delta = dew_point - calculate_dew_point(data_30_min_ago['temperature'], data_30_min_ago['humidity'])
        heat_index_delta = heat_index - calculate_heat_index(data_30_min_ago['temperature'], data_30_min_ago['humidity'])
    else:
        temp_delta = humidity_delta = pressure_delta = iaq_delta = uv_index_delta = light_delta = dew_point_delta = heat_index_delta = None

    # Display metrics with descriptions in rows of two
    st.subheader("Latest Sensor Readings")

    # Function to determine delta class
    def determine_delta_class(delta_value):
        if delta_value is not None:
            if delta_value > 0:
                return "metric-delta-positive"
            elif delta_value < 0:
                return "metric-delta-negative"
            else:
                return "metric-delta-neutral"
        else:
            return "metric-delta-neutral"

    # First row
    col1, col2 = st.columns(2)
    with col1:
        delta_str = f"{temp_delta:+.2f} °C" if temp_delta is not None else "N/A"
        delta_class = determine_delta_class(temp_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Temperature</div>
                <div class="metric-value">{latest_data['temperature']:.2f} °C</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{temp_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        delta_str = f"{humidity_delta:+.2f} %" if humidity_delta is not None else "N/A"
        delta_class = determine_delta_class(humidity_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Humidity</div>
                <div class="metric-value">{latest_data['humidity']:.2f} %</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{humidity_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Second row
    col3, col4 = st.columns(2)
    with col3:
        delta_str = f"{pressure_delta:+.2f} hPa" if pressure_delta is not None else "N/A"
        delta_class = determine_delta_class(pressure_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Pressure</div>
                <div class="metric-value">{latest_data['pressure']:.2f} hPa</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{pressure_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        delta_str = f"{iaq_delta:+.2f}" if iaq_delta is not None else "N/A"
        delta_class = determine_delta_class(iaq_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Indoor Air Quality (IAQ)</div>
                <div class="metric-value">{iaq:.2f}</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{iaq_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Third row
    col5, col6 = st.columns(2)
    with col5:
        delta_str = f"{uv_index_delta:+.2f}" if uv_index_delta is not None else "N/A"
        delta_class = determine_delta_class(uv_index_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">UV Index</div>
                <div class="metric-value">{uv_index:.2f}</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{uv_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col6:
        delta_str = f"{light_delta:+.2f} lux" if light_delta is not None else "N/A"
        delta_class = determine_delta_class(light_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Ambient Light</div>
                <div class="metric-value">{latest_data['ambient_light']:.2f} lux</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{light_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Fourth row
    col7, col8 = st.columns(2)
    with col7:
        delta_str = f"{dew_point_delta:+.2f} °C" if dew_point_delta is not None else "N/A"
        delta_class = determine_delta_class(dew_point_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Dew Point</div>
                <div class="metric-value">{dew_point:.2f} °C</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{dew_point_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col8:
        delta_str = f"{heat_index_delta:+.2f} °C" if heat_index_delta is not None else "N/A"
        delta_class = determine_delta_class(heat_index_delta)
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Heat Index</div>
                <div class="metric-value">{heat_index:.2f} °C</div>
                <div class="{delta_class}">Change: {delta_str}</div>
                <div class="metric-description">{heat_index_desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Display timestamp
    st.write(f"**Timestamp:** {latest_data['Timestamp']}")

else:
    st.warning("No data available yet.")
