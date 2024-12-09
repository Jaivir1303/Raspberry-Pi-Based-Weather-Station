import asyncio
import websockets
import json
import sqlite3
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import pytz
import os

# SQLite setup (existing code)
conn = sqlite3.connect('/home/jaivir1303/myproject/RaspberryPi-Weather-Station/project/weather_data.db')
cursor = conn.cursor()

# Create a table for storing data if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_data (
        Timestamp TEXT,
        Temperature REAL,
        Humidity REAL,
        Pressure REAL,
        AQI REAL,
        UV_Data REAL,
        Ambient_Light REAL
    )
''')
conn.commit()

# InfluxDB connection details
token = os.getenv("INFLUXDB_TOKEN")
org = "BTP Project"
bucket = "Weather Data"
url = "http://localhost:8086"

# Initialize InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
 
# WebSocket URL
WEBSOCKET_URL = "ws://localhost:6789"

# Define your local timezone
local_tz = pytz.timezone('Asia/Kolkata')  # Replace with your local timezone

async def fetch_and_store_data():
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                # Add timestamp if not present
                data['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")

                # Insert the data into the SQLite database
                cursor.execute('''
                    INSERT INTO weather_data (Timestamp, Temperature, Humidity, Pressure, AQI, UV_Data, Ambient_Light)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['timestamp'],
                    data['temperature'],
                    data['humidity'],
                    data['pressure'],
                    data['AQI'],
                    data['uv_data'],
                    data['ambient_light']
                ))
                conn.commit()

                # Get the current local time with timezone
                local_time = datetime.now(local_tz)

                # Prepare data point for InfluxDB
                point = Point("environment") \
                    .tag("location", "office") \
                    .field("temperature", data['temperature']) \
                    .field("humidity", data['humidity']) \
                    .field("pressure", data['pressure']) \
                    .field("gas_resistance", data['AQI']) \
                    .field("uv_data", data['uv_data']) \
                    .field("ambient_light", data['ambient_light']) \
                    .time(local_time)

                # Write data point to InfluxDB
                write_api.write(bucket=bucket, org=org, record=point)

                # Wait before fetching the next data point
                await asyncio.sleep(1)  # Adjust delay as needed
    except Exception as e:
        print(f"Error fetching data: {e}")
    finally:
        # Close database connections
        conn.close()
        client.close()

if __name__ == "__main__":
    asyncio.run(fetch_and_store_data())

