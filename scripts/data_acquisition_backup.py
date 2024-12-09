import asyncio
import websockets
import json
import sqlite3
import time

# Set up SQLite database connection
conn = sqlite3.connect('/home/jaivir1303/myproject/RaspberryPi-Weather-Station/project/weather_data.db')
cursor = conn.cursor()

# Create a table for storing data if it doesn't exist, including UV Data, AQI, and Ambient Light
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

# WebSocket URL
WEBSOCKET_URL = "ws://localhost:6789"

async def fetch_and_store_data():
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                # Correcting Format of Timestamp
                data['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")

                # Insert the data into the SQLite database, including ambient light
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
                    data['ambient_light']  # Include ambient light data in the database
                ))
                conn.commit()

                await asyncio.sleep(1)  # Adjust delay as needed
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_and_store_data())
