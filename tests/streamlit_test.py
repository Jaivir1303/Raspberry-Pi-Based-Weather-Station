# streamlit_test.py

import streamlit as st
import pandas as pd
from data_processing_test import (
    get_influxdb_client,
    update_df_from_db,
    get_theme_css,
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="InfluxDB Data Test",
    page_icon="🔍",
    layout="wide",
)

# Apply custom CSS styles
theme = "Dark"  # Change to "Light" if you prefer
css_styles = get_theme_css(theme)
st.markdown(css_styles, unsafe_allow_html=True)

# Initialize session state variables if not already done
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.data_fetched = False
    st.session_state.last_fetch_time = None  # Will default to 1970-01-01 in the function

# Get InfluxDB client
client = get_influxdb_client()

# Update data
update_df_from_db(client)

# Check if data was fetched
if st.session_state.data_fetched and not st.session_state.df.empty:
    df = st.session_state.df.copy()
    
    # Display the DataFrame
    st.title("InfluxDB Data Test")
    st.write("Displaying the latest data from InfluxDB:")
    st.dataframe(df)
    
    # Optionally, plot a simple line chart
    st.line_chart(df.set_index('Timestamp')[['temperature', 'humidity', 'pressure']])
else:
    st.warning("No data fetched from InfluxDB.")
