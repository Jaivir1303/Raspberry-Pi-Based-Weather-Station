# utils/data_processing.py

import streamlit as st
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient
import pytz

# Function to get InfluxDB client
@st.cache_resource
def get_influxdb_client():
    """
    Returns a cached InfluxDB client.
    """
    token = "3I3Ur26_bYvoj9JCf9RoHC1qUgj7UO-3jAbbD5N1RMHzH_HLGHcJg9XKshtxoxjX_ioZ3bw3fEo7c3qA8bZ-8w=="  # Replace with your actual token
    org = "BTP Project"
    url = "http://localhost:8086"
    client = InfluxDBClient(url=url, token=token, org=org)
    return client

# Function to update DataFrame from InfluxDB
def update_df_from_db(client):
    """
    Fetches new data from InfluxDB and updates the session state DataFrame.
    """
    if 'last_fetch_time' not in st.session_state or st.session_state['last_fetch_time'] is None:
        st.session_state['last_fetch_time'] = pd.Timestamp('1970-01-01T00:00:00Z')

    query_api = client.query_api()

    # Define your local timezone
    local_tz = pytz.timezone('Asia/Kolkata')  # Replace with your local timezone if different

    # Construct the Flux query
    query = f'''
    from(bucket: "Weather Data")
      |> range(start: {st.session_state['last_fetch_time'].isoformat()})
      |> filter(fn: (r) => r._measurement == "environment")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    '''

    # Execute the query
    df_new = query_api.query_data_frame(query)

    if not df_new.empty:
        # Handle potential index column from InfluxDB result
        if isinstance(df_new.columns[0], str) and df_new.columns[0].startswith('table'):
            df_new = df_new.drop(columns=[df_new.columns[0]])

        # Rename and convert the timestamp column
        df_new = df_new.rename(columns={'_time': 'Timestamp'})
        df_new['Timestamp'] = pd.to_datetime(df_new['Timestamp']).dt.tz_convert(local_tz)

        # Update the session state DataFrame
        if 'df' not in st.session_state or st.session_state.df.empty:
            st.session_state.df = df_new
        else:
            st.session_state.df = pd.concat([st.session_state.df, df_new]).drop_duplicates().reset_index(drop=True)

        # Update the last fetch time
        st.session_state['last_fetch_time'] = df_new['Timestamp'].max()
        st.session_state['data_fetched'] = True

def get_old_data(df, minutes=30):
    """
    Retrieves data from the DataFrame that is older by a specified number of minutes.

    Args:
        df: Pandas DataFrame containing the data.
        minutes: The time difference in minutes to look back.

    Returns:
        The row of data that is older by the specified number of minutes, or None if not available.
    """
    if df.empty:
        return None
    time_diff = pd.Timedelta(minutes=minutes)
    old_timestamp = df['Timestamp'].iloc[-1] - time_diff
    old_data = df[df['Timestamp'] <= old_timestamp]
    if not old_data.empty:
        return old_data.iloc[-1]
    else:
        return None

def calculate_uv_index(uv_raw):
    """
    Converts raw UV data to UV Index.

    Args:
        uv_raw: Raw UV data from the sensor.

    Returns:
        Calculated UV Index.
    """
    # Implement the calibration based on your sensor's datasheet
    # Placeholder conversion; adjust based on actual calibration
    uv_index = uv_raw / 100  # Example conversion factor
    return uv_index

def temperature_description(temp):
    """
    Provides a description based on the temperature value.

    Args:
        temp: Temperature in degrees Celsius.

    Returns:
        A string description of the temperature.
    """
    if temp >= 30:
        return "Hot 🔥"
    elif temp >= 20:
        return "Warm 🌤️"
    elif temp >= 10:
        return "Cool 🌥️"
    else:
        return "Cold ❄️"

def humidity_description(humidity):
    """
    Provides a description based on the humidity value.

    Args:
        humidity: Humidity percentage.

    Returns:
        A string description of the humidity.
    """
    if humidity >= 70:
        return "High Humidity 💦"
    elif humidity >= 40:
        return "Comfortable 😊"
    else:
        return "Dry 🍃"

def aqi_description(aqi):
    """
    Provides a description based on the AQI value.

    Args:
        aqi: Air Quality Index value.

    Returns:
        A string description of the air quality.
    """
    if aqi >= 301:
        return "Hazardous ☠️"
    elif aqi >= 201:
        return "Very Unhealthy 😷"
    elif aqi >= 151:
        return "Unhealthy 🙁"
    elif aqi >= 101:
        return "Unhealthy for Sensitive Groups 😕"
    elif aqi >= 51:
        return "Moderate 😐"
    else:
        return "Good 😊"

def uv_description(uv_index):
    """
    Provides a description based on the UV Index value.

    Args:
        uv_index: UV Index value.

    Returns:
        A string description of the UV exposure level.
    """
    if uv_index >= 11:
        return "Extreme ⚠️"
    elif uv_index >= 8:
        return "Very High 🛑"
    elif uv_index >= 6:
        return "High 🔆"
    elif uv_index >= 3:
        return "Moderate 🌞"
    else:
        return "Low 🌙"

def ambient_light_description(lux):
    """
    Provides a description based on the ambient light intensity.

    Args:
        lux: Ambient light in lux.

    Returns:
        A string description of the ambient light level.
    """
    if lux >= 10000:
        return "Bright Sunlight ☀️"
    elif lux >= 1000:
        return "Daylight 🌤️"
    elif lux >= 500:
        return "Overcast ☁️"
    elif lux >= 100:
        return "Indoor Lighting 💡"
    else:
        return "Dim Light 🌙"

def pressure_description(pressure):
    """
    Provides a description based on the atmospheric pressure.

    Args:
        pressure: Atmospheric pressure in hPa.

    Returns:
        A string description of the weather trend.
    """
    if pressure >= 1020:
        return "High Pressure 🌞"
    elif pressure >= 1000:
        return "Normal Pressure 🌤️"
    else:
        return "Low Pressure 🌧️"

def calculate_dew_point(temp, humidity):
    """
    Calculates the dew point based on temperature and humidity.

    Args:
        temp: Temperature in degrees Celsius.
        humidity: Humidity percentage.

    Returns:
        Dew point temperature in degrees Celsius.
    """
    # Constants for the calculation
    a = 17.27
    b = 237.7
    alpha = ((a * temp) / (b + temp)) + np.log(humidity / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return dew_point

def dew_point_description(dew_point):
    """
    Provides a description based on the dew point temperature.

    Args:
        dew_point: Dew point in degrees Celsius.

    Returns:
        A string description of the comfort level.
    """
    if dew_point >= 24:
        return "Severely Uncomfortable 🥵"
    elif dew_point >= 20:
        return "Uncomfortable 😓"
    elif dew_point >= 16:
        return "Somewhat Comfortable 🙂"
    elif dew_point >= 10:
        return "Comfortable 😊"
    else:
        return "Dry 🍃"

def calculate_heat_index(temp, humidity):
    """
    Calculates the heat index based on temperature and humidity.

    Args:
        temp: Temperature in degrees Celsius.
        humidity: Humidity percentage.

    Returns:
        Heat index in degrees Celsius.
    """
    # Convert temperature to Fahrenheit for calculation
    temp_f = temp * 9/5 + 32
    hi = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094))

    if hi >= 80:
        # Use the full regression equation
        hi = -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity \
             - 0.22475541 * temp_f * humidity - 0.00683783 * temp_f**2 \
             - 0.05481717 * humidity**2 + 0.00122874 * temp_f**2 * humidity \
             + 0.00085282 * temp_f * humidity**2 - 0.00000199 * temp_f**2 * humidity**2

        # Adjustments
        if (humidity < 13) and (80 <= temp_f <= 112):
            adj = ((13 - humidity) / 4) * np.sqrt((17 - abs(temp_f - 95.)) / 17)
            hi -= adj
        elif (humidity > 85) and (80 <= temp_f <= 87):
            adj = ((humidity - 85) / 10) * ((87 - temp_f) / 5)
            hi += adj

    # Convert back to Celsius
    heat_index = (hi - 32) * 5/9
    return heat_index

def heat_index_description(heat_index):
    """
    Provides a description based on the heat index.

    Args:
        heat_index: Heat index in degrees Celsius.

    Returns:
        A string description of the heat index level.
    """
    if heat_index >= 54:
        return "Extreme Danger ☠️"
    elif heat_index >= 41:
        return "Danger 🔥"
    elif heat_index >= 32:
        return "Extreme Caution 😓"
    elif heat_index >= 27:
        return "Caution 😐"
    else:
        return "Comfortable 😊"

def calculate_iaq(r_gas, humidity):
    """
    Estimates the Indoor Air Quality (IAQ) based on gas resistance and humidity.

    Args:
        r_gas: Gas resistance value from BME680 in Ohms.
        humidity: Relative humidity percentage.

    Returns:
        Estimated IAQ value.
    """
    import math
    # Use base 10 logarithm
    iaq = math.log10(r_gas) + 0.04 * humidity
    return iaq

def get_theme_css(theme):
    """
    Returns CSS styles based on the selected theme.

    Args:
        theme: A string indicating the theme ("Light" or "Dark").

    Returns:
        A string containing CSS styles.
    """
    if theme == "Light":
        # Light theme colors
        background_color = "#FFFFFF"
        text_color = "#000000"
        title_color = "#000000"
        container_background_color = "#F0F0F0"
        metric_label_color = "#555555"
        metric_value_color = "#000000"
        metric_delta_positive_color = "#008000"  # Green
        metric_delta_negative_color = "#FF0000"  # Red
        metric_delta_neutral_color = "#000000"   # Black
        metric_description_color = "#333333"
        sidebar_background_color = "#F8F8F8"
        sidebar_text_color = "#000000"
        sidebar_link_color = "#0000EE"
        selectbox_background_color = "#FFFFFF"
        selectbox_text_color = "#000000"
        button_background_color = "#FFFFFF"
        button_text_color = "#000000"
        button_border_color = "#000000"
    else:
        # Dark theme colors
        background_color = "#0E1117"
        text_color = "#FFFFFF"
        title_color = "#FFFFFF"
        container_background_color = "#1E1E1E"
        metric_label_color = "#AAAAAA"
        metric_value_color = "#FFFFFF"
        metric_delta_positive_color = "#00FF00"  # Bright Green
        metric_delta_negative_color = "#FF4500"  # Orange Red
        metric_delta_neutral_color = "#FFFFFF"   # White
        metric_description_color = "#DDDDDD"
        sidebar_background_color = "#1E1E1E"
        sidebar_text_color = "#FFFFFF"
        sidebar_link_color = "#1E90FF"
        selectbox_background_color = "#1E1E1E"
        selectbox_text_color = "#FFFFFF"
        button_background_color = "#1E1E1E"
        button_text_color = "#FFFFFF"
        button_border_color = "#FFFFFF"

    css = f"""
    <style>
    /* Background */
    .stApp {{
        background-color: {background_color};
    }}

    /* Main content text color - Target specific text elements */
    .stApp div[data-testid="stVerticalBlock"] p,
    .stApp div[data-testid="stVerticalBlock"] span,
    .stApp div[data-testid="stVerticalBlock"] ul,
    .stApp div[data-testid="stVerticalBlock"] li,
    .stApp div[data-testid="stVerticalBlock"] h1,
    .stApp div[data-testid="stVerticalBlock"] h2,
    .stApp div[data-testid="stVerticalBlock"] h3,
    .stApp div[data-testid="stVerticalBlock"] h4,
    .stApp div[data-testid="stVerticalBlock"] h5,
    .stApp div[data-testid="stVerticalBlock"] h6 {{
        color: {text_color};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_background_color};
        color: {sidebar_text_color};
    }}
    section[data-testid="stSidebar"] * {{
        color: {sidebar_text_color};
    }}
    section[data-testid="stSidebar"] a {{
        color: {sidebar_link_color};
    }}

    /* Title Styling */
    .title {{
        font-size: 2.5em;
        color: {title_color};
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
        font-family: 'Montserrat', sans-serif;
        margin-bottom: 20px;
    }}

    /* Metric Styling */
    .metric-container {{
        background-color: {container_background_color};
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.4);
    }}

    .metric-label {{
        color: {metric_label_color};
        font-size: 1.2em;
    }}

    .metric-value {{
        color: {metric_value_color};
        font-size: 2em;
    }}

    /* Delta Value Styling - More Specific Selectors */
    .metric-container .metric-delta-positive {{
        color: {metric_delta_positive_color};
        font-size: 1em;
    }}
    .metric-container .metric-delta-negative {{
        color: {metric_delta_negative_color};
        font-size: 1em;
    }}
    .metric-container .metric-delta-neutral {{
        color: {metric_delta_neutral_color};
        font-size: 1em;
    }}

    /* Metric Description */
    .metric-description {{
        color: {metric_description_color};
        font-size: 1em;
        margin-top: 10px;
    }}

    /* Text Styling */
    .custom-text {{
        color: {text_color};
        font-size: 1.2em;
    }}

    /* Selectbox Styling */
    div[data-baseweb="select"] > div {{
        background-color: {selectbox_background_color};
        color:{selectbox_text_color};
    }}
    div[data-baseweb="select"] input {{
        background-color: {selectbox_background_color};
        color: {selectbox_text_color};
    }}
    div[data-baseweb="select"] svg {{
        fill: {selectbox_text_color};
    }}
    /* Dropdown menu options */
    ul[data-baseweb="menu"] {{
        background-color: {selectbox_background_color};
        color: {selectbox_text_color};
    }}
    ul[data-baseweb="menu"] li {{
        color: {selectbox_text_color};
    }}

    /* Button Styling */
    div.stButton > button {{
        background-color: {button_background_color};
        color: {button_text_color};
        border: 1px solid {button_border_color};
        padding: 0.5em 1em;
        border-radius: 5px;
    }}

    /* Adjust hover and active states */
    div.stButton > button:hover {{
        background-color: {container_background_color};
    }}

    div.stButton > button:active {{
        background-color: {container_background_color};
    }}

    </style>
    """
    return css
