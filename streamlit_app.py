# streamlit_app.py

import pandas as pd
import streamlit as st
import plotly.graph_objs as go
import sqlite3
import time
from streamlit_autorefresh import st_autorefresh
from utils.data_processing import get_db_connection, update_df_from_db, get_theme_css
from utils.sidebar import render_sidebar

# Set Streamlit page configuration
st.set_page_config(
    page_title="Real-Time Weather Data Dashboard",
    page_icon="🌤️",
    layout="wide",
)

# Automatically refresh every 5 seconds
st_autorefresh(interval=5000, key="data_refresh")

# Render the sidebar
render_sidebar()

# Get the selected theme from session state
theme = st.session_state.get('theme', 'Dark')
css_styles = get_theme_css(theme)
st.markdown(css_styles, unsafe_allow_html=True)

# Main title with custom styling
st.markdown("<h1 class='title'>Real-Time Weather Data Dashboard</h1>", unsafe_allow_html=True)

# Initialize session state variables if not already done
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.data_fetched = False
    st.session_state.last_fetch_time = '1970-01-01 00:00:00'

# Get database connection
conn = get_db_connection()

# Update data
update_df_from_db(conn)

# Function to get old data for comparison
def get_old_data(df, minutes=30):
    if df.empty:
        return None
    time_diff = pd.Timedelta(minutes=minutes)
    old_timestamp = df['Timestamp'].iloc[-1] - time_diff
    old_data = df[df['Timestamp'] <= old_timestamp]
    if not old_data.empty:
        return old_data.iloc[-1]
    else:
        return None

if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df
    latest_data = df.iloc[-1]

    # Calculate the 30-minute offset
    old_data = get_old_data(df, minutes=30)
    if old_data is not None:
        temp_delta = latest_data['Temperature'] - old_data['Temperature']
        humidity_delta = latest_data['Humidity'] - old_data['Humidity']
        pressure_delta = latest_data['Pressure'] - old_data['Pressure']
    else:
        temp_delta = humidity_delta = pressure_delta = None

    # Display metrics with custom styling
    col1, col2, col3 = st.columns(3)

    with col1:
        delta_str = f"{temp_delta:+.2f} °C" if temp_delta is not None else "N/A"
        if temp_delta is not None:
            if temp_delta > 0:
                delta_class = "metric-delta-positive"
            elif temp_delta < 0:
                delta_class = "metric-delta-negative"
            else:
                delta_class = "metric-delta-neutral"
        else:
            delta_class = "metric-delta-neutral"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Temperature</div>
                <div class="metric-value">{latest_data['Temperature']:.2f} °C</div>
                <div class="{delta_class}">Change: {delta_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        delta_str = f"{humidity_delta:+.2f} %" if humidity_delta is not None else "N/A"
        if humidity_delta is not None:
            if humidity_delta > 0:
                delta_class = "metric-delta-positive"
            elif humidity_delta < 0:
                delta_class = "metric-delta-negative"
            else:
                delta_class = "metric-delta-neutral"
        else:
            delta_class = "metric-delta-neutral"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Humidity</div>
                <div class="metric-value">{latest_data['Humidity']:.2f} %</div>
                <div class="{delta_class}">Change: {delta_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        delta_str = f"{pressure_delta:+.2f} hPa" if pressure_delta is not None else "N/A"
        if pressure_delta is not None:
            if pressure_delta > 0:
                delta_class = "metric-delta-positive"
            elif pressure_delta < 0:
                delta_class = "metric-delta-negative"
            else:
                delta_class = "metric-delta-neutral"
        else:
            delta_class = "metric-delta-neutral"
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">Pressure</div>
                <div class="metric-value">{latest_data['Pressure']:.2f} hPa</div>
                <div class="{delta_class}">Change: {delta_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Plot graphs
    st.subheader("Temperature, Humidity, and Pressure Over Time")

    # Plot theme settings
    if theme == "Light":
        plot_bgcolor = 'rgb(240,240,240)'
        paper_bgcolor = 'rgb(240,240,240)'
        font_color = 'black'
    else:
        plot_bgcolor = 'rgb(17,17,17)'
        paper_bgcolor = 'rgb(17,17,17)'
        font_color = 'white'

    fig = go.Figure()

    # Temperature
    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['Temperature'],
        mode='lines',
        name='Temperature (°C)',
        line=dict(color='red'),
        yaxis='y1'
    ))

    # Humidity
    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['Humidity'],
        mode='lines',
        name='Humidity (%)',
        line=dict(color='blue'),
        yaxis='y2'
    ))

    # Pressure
    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=df['Pressure'],
        mode='lines',
        name='Pressure (hPa)',
        line=dict(color='green'),
        yaxis='y3'
    ))

    # Update layout
    fig.update_layout(
        xaxis=dict(domain=[0.1, 0.9], title='Time', titlefont=dict(color=font_color), tickfont=dict(color=font_color)),
        yaxis=dict(
            title="Temperature (°C)",
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor="free",
            position=0.05
        ),
        yaxis2=dict(
            title="Humidity (%)",
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue'),
            anchor="x",
            overlaying="y",
            side="left",
            position=0
        ),
        yaxis3=dict(
            title="Pressure (hPa)",
            titlefont=dict(color='green'),
            tickfont=dict(color='green'),
            anchor="free",
            overlaying="y",
            side="right",
            position=0.95
        ),
        legend=dict(
            x=0,
            y=1.1,
            orientation="h",
            font=dict(color=font_color)
        ),
        plot_bgcolor=plot_bgcolor,
        paper_bgcolor=paper_bgcolor,
        font=dict(color=font_color),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display timestamp
    st.write(f"**Last Updated:** {latest_data['Timestamp']}")

    # Footer
    st.markdown("<div style='text-align: center; color: gray;'>Data is updated in real-time from the sensors.</div>", unsafe_allow_html=True)
else:
    st.warning("No data available yet.")
