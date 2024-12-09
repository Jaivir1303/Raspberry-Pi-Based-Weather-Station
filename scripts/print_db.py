# scripts/print_db.py

import sqlite3
import pandas as pd

def print_last_n_entries(db_path='/home/jaivir1303/myproject/RaspberryPi-Weather-Station/project/weather_data.db', n=20):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch the last n entries ordered by Timestamp
    cursor.execute(f'''
        SELECT * FROM weather_data ORDER BY Timestamp DESC LIMIT {n}
    ''')
    rows = cursor.fetchall()
    
    if rows:
        # Assuming the same column order as in your table creation
        df = pd.DataFrame(rows, columns=[
            'Timestamp',
            'Temperature',
            'Humidity',
            'Pressure',
            'AQI',
            'UV_Data',
            'Ambient_Light'
        ])
        print(df)
    else:
        print("No data found in the database.")
    
    conn.close()

if __name__ == "__main__":
    print_last_n_entries()
