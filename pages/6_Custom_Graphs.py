# pages/6_Custom_Graphs.py

import streamlit as st
import pandas as pd
from utils.data_processing_influx import (
    get_influxdb_client,
    update_df_from_db,
    get_theme_css
)
from utils.sidebar import render_sidebar
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Set page configuration
st.set_page_config(
    page_title="Custom Graphs",
    page_icon="📊",
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
st.markdown("<h1 class='title'>Custom Graphs</h1>", unsafe_allow_html=True)

# Initialize session state variables if not already done
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.data_fetched = False
    st.session_state.last_fetch_time = None  # Will default to 1970-01-01 in the function

# Get InfluxDB client
client = get_influxdb_client()

# Add manual refresh button
if st.button("Refresh Data"):
    update_df_from_db(client)

# Ensure data is updated
if not st.session_state.data_fetched:
    update_df_from_db(client)

# Debugging: Display the DataFrame
# st.write("DataFrame after fetching data:")
# st.write(st.session_state.df.head())

# Display analysis tools
if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # Ensure data is numeric
    metrics = ['temperature', 'humidity', 'pressure', 'gas_resistance', 'uv_data', 'ambient_light']
    for metric in metrics:
        df[metric] = pd.to_numeric(df[metric], errors='coerce')

    # Drop rows with NaN values in the selected metrics
    df = df.dropna(subset=metrics)

    # Add 'Time' as an option for X-axis metric
    x_axis_options = ['Time'] + metrics

    # User selections
    st.markdown("### Select Metrics and Plot Type")

    col1, col2 = st.columns(2)
    with col1:
        metric_x = st.selectbox('Select X-axis Metric', x_axis_options)
    with col2:
        # If 'Time' is selected for X-axis, Y-axis metrics can be any of the metrics
        # If a metric is selected for X-axis, exclude it from Y-axis options
        if metric_x == 'Time':
            metrics_y_options = metrics
        else:
            metrics_y_options = [m for m in metrics if m != metric_x]
        metric_y = st.selectbox('Select Y-axis Metric', metrics_y_options)

    plot_type = st.selectbox('Select Plot Type', ['Line Plot', 'Scatter Plot', 'Bar Chart', 'Correlation Plot'])

    # Time period selection
    min_time = df['Timestamp'].min().to_pydatetime()
    max_time = df['Timestamp'].max().to_pydatetime()
    time_range = st.slider(
        'Select Time Range',
        min_value=min_time,
        max_value=max_time,
        value=(min_time, max_time),
        format="YYYY-MM-DD HH:mm"
    )

    # Filter data based on time range
    mask = (df['Timestamp'] >= time_range[0]) & (df['Timestamp'] <= time_range[1])
    df_filtered = df.loc[mask]

    # Check if the filtered data is empty
    if df_filtered.empty:
        st.warning("No data available for the selected time range.")
    else:
        st.subheader(f"{plot_type} of {metric_y} vs {metric_x}")

        # Plot theme settings
        if theme == "Light":
            plot_bgcolor = 'rgb(240,240,240)'
            paper_bgcolor = 'rgb(240,240,240)'
            font_color = 'black'
        else:
            plot_bgcolor = 'rgb(17,17,17)'
            paper_bgcolor = 'rgb(17,17,17)'
            font_color = 'white'

        # Set x-axis data
        if metric_x == 'Time':
            x_data = df_filtered['Timestamp']
            x_title = 'Time'
        else:
            x_data = df_filtered[metric_x]
            x_title = metric_x

        # Generate the plot
        if plot_type == 'Scatter Plot':
            fig = px.scatter(df_filtered, x=x_data, y=df_filtered[metric_y])
            fig.update_traces(mode='markers')
        elif plot_type == 'Line Plot':
            fig = px.line(df_filtered, x=x_data, y=df_filtered[metric_y])
        elif plot_type == 'Bar Chart':
            fig = px.bar(df_filtered, x=x_data, y=df_filtered[metric_y])
        elif plot_type == 'Correlation Plot':
            # Plot scatter plot with trendline
            fig = px.scatter(df_filtered, x=x_data, y=df_filtered[metric_y], trendline="ols")
        else:
            st.error("Invalid plot type selected.")
            fig = None

        if fig:
            fig.update_layout(
                xaxis_title=x_title,
                yaxis_title=metric_y,
                plot_bgcolor=plot_bgcolor,
                paper_bgcolor=paper_bgcolor,
                font=dict(color=font_color),
                xaxis=dict(
                    tickfont=dict(color=font_color),
                    titlefont=dict(color=font_color),
                    gridcolor='gray',
                    showgrid=True
                ),
                yaxis=dict(
                    tickfont=dict(color=font_color),
                    titlefont=dict(color=font_color),
                    gridcolor='gray',
                    showgrid=True
                )
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available yet.")
