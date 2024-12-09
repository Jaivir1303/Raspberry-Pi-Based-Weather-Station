# pages/2_Weather_Metrics.py

import streamlit as st
import pandas as pd
from utils.data_processing_influx import (
    get_influxdb_client,
    update_df_from_db,
    get_theme_css
)
from utils.sidebar import render_sidebar
from streamlit_autorefresh import st_autorefresh
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="Weather Metrics",
    page_icon="🌡️",
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
st.markdown("<h1 class='title'>Weather Metrics</h1>", unsafe_allow_html=True)

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

# Display metrics and graphs
if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Ensure data is numeric
    metrics = ['temperature', 'humidity', 'pressure']
    for metric in metrics:
        df[metric] = pd.to_numeric(df[metric], errors='coerce')

    # Drop rows with NaN values in the selected metrics
    df_clean = df.dropna(subset=metrics)

    latest_data = df_clean.iloc[-1]

    # Data from 30 minutes ago
    data_30_min_ago = get_data_minutes_ago(df_clean, 30)

    # Calculate delta values for Temperature, Humidity, Pressure
    if data_30_min_ago is not None:
        temp_delta = latest_data['temperature'] - data_30_min_ago['temperature']
        temp_percent_change = (temp_delta / data_30_min_ago['temperature']) * 100 if data_30_min_ago['temperature'] != 0 else 0

        humidity_delta = latest_data['humidity'] - data_30_min_ago['humidity']
        humidity_percent_change = (humidity_delta / data_30_min_ago['humidity']) * 100 if data_30_min_ago['humidity'] != 0 else 0

        pressure_delta = latest_data['pressure'] - data_30_min_ago['pressure']
        pressure_percent_change = (pressure_delta / data_30_min_ago['pressure']) * 100 if data_30_min_ago['pressure'] != 0 else 0
    else:
        temp_delta = humidity_delta = pressure_delta = None
        temp_percent_change = humidity_percent_change = pressure_percent_change = None

    # Display metrics with percentage changes
    st.subheader("Current Weather Metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        delta_str = f"{temp_percent_change:+.2f}%" if temp_percent_change is not None else "N/A"
        delta_class = "metric-delta-neutral"
        if temp_percent_change is not None:
            if temp_percent_change > 0:
                delta_class = "metric-delta-positive"
            elif temp_percent_change < 0:
                delta_class = "metric-delta-negative"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Temperature</div>
                <div class="metric-value">{latest_data['temperature']:.2f} °C</div>
                <div class="{delta_class}">Change: {delta_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        delta_str = f"{humidity_percent_change:+.2f}%" if humidity_percent_change is not None else "N/A"
        delta_class = "metric-delta-neutral"
        if humidity_percent_change is not None:
            if humidity_percent_change > 0:
                delta_class = "metric-delta-positive"
            elif humidity_percent_change < 0:
                delta_class = "metric-delta-negative"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Humidity</div>
                <div class="metric-value">{latest_data['humidity']:.2f} %</div>
                <div class="{delta_class}">Change: {delta_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        delta_str = f"{pressure_percent_change:+.2f}%" if pressure_percent_change is not None else "N/A"
        delta_class = "metric-delta-neutral"
        if pressure_percent_change is not None:
            if pressure_percent_change > 0:
                delta_class = "metric-delta-positive"
            elif pressure_percent_change < 0:
                delta_class = "metric-delta-negative"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Pressure</div>
                <div class="metric-value">{latest_data['pressure']:.2f} hPa</div>
                <div class="{delta_class}">Change: {delta_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Plot line graphs for Temperature, Humidity, Pressure
    st.subheader("Weather Metrics Over Time")

    # Plot theme settings
    if theme == "Light":
        plot_bgcolor = 'rgb(240,240,240)'
        paper_bgcolor = 'rgb(240,240,240)'
        font_color = 'black'
        axis_color = "#000000"
    else:
        plot_bgcolor = 'rgb(17,17,17)'
        paper_bgcolor = 'rgb(17,17,17)'
        font_color = 'white'
        axis_color = "#FFFFFF"

    # Temperature Graph
    st.markdown("#### Temperature Over Time")
    fig_temp = px.line(df_clean, x='Timestamp', y='temperature', color_discrete_sequence=['red'])
    fig_temp.update_layout(
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        plot_bgcolor=plot_bgcolor,
        paper_bgcolor=paper_bgcolor,
        font=dict(color=font_color),
        xaxis=dict(
            tickformat='%H:%M',
            titlefont=dict(color=font_color),
            tickfont=dict(color=font_color),
            linecolor=axis_color,
            showgrid=False),
        yaxis=dict(
            titlefont=dict(color=font_color),
            tickfont=dict(color=font_color),
            linecolor=axis_color,
            showgrid=False
        )
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    # Humidity Graph
    st.markdown("#### Humidity Over Time")
    fig_humidity = px.line(df_clean, x='Timestamp', y='humidity', color_discrete_sequence=['blue'])
    fig_humidity.update_layout(
        xaxis_title='Time',
        yaxis_title='Humidity (%)',
        plot_bgcolor=plot_bgcolor,
        paper_bgcolor=paper_bgcolor,
        font=dict(color=font_color),
        xaxis=dict(
            tickformat="%H:%M",
            titlefont=dict(color=font_color),
            tickfont=dict(color=font_color),
            linecolor=axis_color,
            showgrid=False
        ),
        yaxis=dict(
            titlefont=dict(color=font_color),
            tickfont=dict(color=font_color),
            linecolor=axis_color,
            showgrid=False
        )
    )
    st.plotly_chart(fig_humidity, use_container_width=True)

    # Pressure Graph
    st.markdown("#### Pressure Over Time")
    fig_pressure = px.line(df_clean, x='Timestamp', y='pressure', color_discrete_sequence=['green'])
    fig_pressure.update_layout(
        xaxis_title='Time',
        yaxis_title='Pressure (hPa)',
        plot_bgcolor=plot_bgcolor,
        paper_bgcolor=paper_bgcolor,
        font=dict(color=font_color),
        xaxis=dict(
            tickformat="%H:%M",
            titlefont=dict(color=font_color),
            tickfont=dict(color=font_color),
            linecolor=axis_color,
            showgrid=False
        ),
        yaxis=dict(
            titlefont=dict(color=font_color),
            tickfont=dict(color=font_color),
            linecolor=axis_color,
            showgrid=False
        )
    )
    st.plotly_chart(fig_pressure, use_container_width=True)

    # Add a gap
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Display correlation values between Temperature, Humidity, and Pressure
    st.subheader("Correlation Values")

    # Calculate correlation matrix
    corr_matrix = df_clean[['temperature', 'humidity', 'pressure']].corr()

    # Display correlation matrix as a table with proper formatting
    st.table(corr_matrix.style.background_gradient(cmap='coolwarm').format(precision=2))

else:
    st.warning("No data available yet.")
