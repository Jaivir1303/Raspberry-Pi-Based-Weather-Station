# tests/setup_sqlite.py
import sqlite3

def setup_sqlite_db(db_path='weather_data.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            ambient_light REAL,
            uv REAL,
            gas_resistance REAL
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_sqlite_db()
    print("SQLite database setup complete.")
