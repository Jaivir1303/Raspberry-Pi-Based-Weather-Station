# pages/3_Air_Quality.py

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_processing_influx import (
    get_influxdb_client,
    update_df_from_db,
    calculate_iaq,
    get_theme_css
)
from utils.sidebar import render_sidebar
from streamlit_autorefresh import st_autorefresh
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="Air Quality",
    page_icon="🌬️",
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
st.markdown("<h1 class='title'>Air Quality</h1>", unsafe_allow_html=True)

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

# Display Air Quality data
if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Ensure data is numeric
    metrics = ['gas_resistance', 'humidity']
    for metric in metrics:
        df[metric] = pd.to_numeric(df[metric], errors='coerce')

    # Drop rows with NaN values in the selected metrics
    df_clean = df.dropna(subset=metrics)

    # Calculate IAQ using the calculate_iaq function
    df_clean['IAQ'] = df_clean.apply(lambda row: calculate_iaq(row['gas_resistance'], row['humidity']), axis=1)

    latest_data = df_clean.iloc[-1]

    # Determine IAQ Category
    def get_iaq_category(iaq_value):
        if iaq_value <= 50:
            return "Excellent", "#00FF00"
        elif iaq_value <= 100:
            return "Good", "#7FFF00"
        elif iaq_value <= 150:
            return "Lightly Polluted", "#FFFF00"
        elif iaq_value <= 200:
            return "Moderately Polluted", "#FF7F00"
        elif iaq_value <= 300:
            return "Heavily Polluted", "#FF0000"
        else:
            return "Severely Polluted", "#8B0000"

    iaq_category, category_color = get_iaq_category(latest_data['IAQ'])

    # Display current IAQ value
    st.subheader("Current Indoor Air Quality")

    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-label">IAQ</div>
            <div class="metric-value">{latest_data['IAQ']:.2f}</div>
            <div class="metric-category" style="color: {category_color};">{iaq_category}</div>
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

    # Plot IAQ over time
    st.subheader("IAQ Over Time")

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
        fig_iaq = px.line(df_filtered, x='Timestamp', y='IAQ', color_discrete_sequence=['cyan'])
        fig_iaq.update_layout(
            xaxis_title='Time',
            yaxis_title='IAQ',
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
        st.plotly_chart(fig_iaq, use_container_width=True)

    # Plot Gas Resistance over time
    st.subheader("Gas Resistance Over Time")
    fig_gas = px.line(df_filtered, x='Timestamp', y='gas_resistance', color_discrete_sequence=['magenta'])
    fig_gas.update_layout(
        xaxis_title='Time',
        yaxis_title='Gas Resistance (Ω)',
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
    st.plotly_chart(fig_gas, use_container_width=True)

    # Additional Information
    st.subheader("Understanding IAQ")
    st.markdown("""
    **Indoor Air Quality (IAQ)** is a measure of the air quality within and around buildings as it relates to the health and comfort of building occupants.

    **Categories:**

    - **Excellent (0-50):** Air quality is considered satisfactory, and air pollution poses little or no risk.
    - **Good (51-100):** Air quality is acceptable; however, some pollutants may slightly affect very few hypersensitive individuals.
    - **Lightly Polluted (101-150):** Sensitive individuals may experience health effects. The general public is not likely to be affected.
    - **Moderately Polluted (151-200):** Everyone may begin to experience health effects; sensitive groups may experience more serious health effects.
    - **Heavily Polluted (201-300):** Health warnings of emergency conditions. The entire population is more likely to be affected.
    - **Severely Polluted (301+):** Emergency conditions. The entire population is likely to be affected more seriously.

    **Note:** The IAQ values are estimations based on gas resistance measurements and a simplified calculation. For more accurate assessments, professional-grade sensors and calibrated algorithms are recommended.
    """)
else:
    st.warning("No data available yet.")
