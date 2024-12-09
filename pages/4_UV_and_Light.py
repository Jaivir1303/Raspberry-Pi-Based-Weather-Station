# pages/4_UV_and_Light.py

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_processing_influx import (
    get_influxdb_client,
    update_df_from_db,
    calculate_uv_index,
    uv_description,
    get_theme_css
)
from utils.sidebar import render_sidebar
from streamlit_autorefresh import st_autorefresh
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="UV and Light",
    page_icon="☀️",
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
st.markdown("<h1 class='title'>UV and Light</h1>", unsafe_allow_html=True)

# Initialize session state variables if not already done
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.data_fetched = False
    st.session_state.last_fetch_time = None  # Will default to 1970-01-01 in the function

# Get InfluxDB client
client = get_influxdb_client()

# Update data
update_df_from_db(client)

# Debugging: Display the DataFrame
# st.write("DataFrame after fetching data:")
# st.write(st.session_state.df.head())

# Display UV and Light data
if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Ensure data is numeric
    metrics = ['uv_data', 'ambient_light']
    for metric in metrics:
        df[metric] = pd.to_numeric(df[metric], errors='coerce')

    # Drop rows with NaN values in the selected metrics
    df_clean = df.dropna(subset=metrics)

    # Calculate UV Index from 'uv_data' using the function from utils.data_processing_influx
    df_clean['UV_Index'] = df_clean['uv_data'].apply(calculate_uv_index)

    latest_data = df_clean.iloc[-1]

    # Get UV Index description
    uv_category = uv_description(latest_data['UV_Index'])

    # Determine color based on UV Index category
    def get_uv_color(uv_index):
        if uv_index >= 11:
            return "#FF0000"  # Extreme - Red
        elif uv_index >= 8:
            return "#FF4500"  # Very High - OrangeRed
        elif uv_index >= 6:
            return "#FFA500"  # High - Orange
        elif uv_index >= 3:
            return "#FFFF00"  # Moderate - Yellow
        else:
            return "#00FF00"  # Low - Green

    category_color = get_uv_color(latest_data['UV_Index'])

    # Display current UV Index and Ambient Light
    st.subheader("Current UV Index and Ambient Light")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">UV Index</div>
                <div class="metric-value">{latest_data['UV_Index']:.2f}</div>
                <div class="metric-category" style="color: {category_color};">{uv_category}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Ambient Light</div>
                <div class="metric-value">{latest_data['ambient_light']:.2f} lux</div>
            </div>
            """,
            unsafe_allow_html=True
        )

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

    # Plot UV Index over time
    st.subheader("UV Index Over Time")

    # Time range selection
    min_time = df_clean['Timestamp'].min().to_pydatetime()
    max_time = df_clean['Timestamp'].max().to_pydatetime()
    time_range = st.slider(
        'Select Time Range',
        min_value=min_time,
        max_value=max_time,
        value=(min_time, max_time),
        format="YYYY-MM-DD HH:mm"
    )

    # Filter data based on time range
    mask = (df_clean['Timestamp'] >= time_range[0]) & (df_clean['Timestamp'] <= time_range[1])
    df_filtered = df_clean.loc[mask]

    if df_filtered.empty:
        st.warning("No data available for the selected time range.")
    else:
        fig_uv = px.line(df_filtered, x='Timestamp', y='UV_Index', color_discrete_sequence=['#FFA500'])
        fig_uv.update_layout(
            xaxis_title='Time',
            yaxis_title='UV Index',
            plot_bgcolor=plot_bgcolor,
            paper_bgcolor=paper_bgcolor,
            font=dict(color=font_color),
            xaxis=dict(
                tickformat=('%H:%M'),
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
        st.plotly_chart(fig_uv, use_container_width=True)

    # Plot Ambient Light over time
    st.subheader("Ambient Light Over Time")

    if df_filtered.empty:
        st.warning("No data available for the selected time range.")
    else:
        fig_light = px.line(df_filtered, x='Timestamp', y='ambient_light', color_discrete_sequence=['#00FFFF'])
        fig_light.update_layout(
            xaxis_title='Time',
            yaxis_title='Ambient Light (lux)',
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
                showgrid=False)
        )
        st.plotly_chart(fig_light, use_container_width=True)

    # Health Advisory Messages based on UV Index
    st.subheader("Health Advisory")
    uv_index = latest_data['UV_Index']
    uv_advisory = ""

    if uv_index >= 11:
        uv_advisory = "⚠️ **Extreme UV exposure risk! Avoid sun exposure and seek shade.**"
    elif uv_index >= 8:
        uv_advisory = "🛑 **Very High UV exposure risk! Wear protective clothing, sunglasses, and apply sunscreen.**"
    elif uv_index >= 6:
        uv_advisory = "🔆 **High UV exposure risk! Reduce time in the sun during midday hours and seek shade.**"
    elif uv_index >= 3:
        uv_advisory = "🌞 **Moderate UV exposure risk! Stay in shade near midday when the sun is strongest.**"
    else:
        uv_advisory = "🌙 **Low UV exposure risk. Enjoy your time outside!**"

    st.markdown(uv_advisory)

else:
    st.warning("No data available yet.")
