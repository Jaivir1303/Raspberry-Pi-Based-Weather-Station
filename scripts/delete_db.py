import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('/home/jaivir1303/myproject/RaspberryPi-Weather-Station/project/weather_data.db')
cursor = conn.cursor()

# Delete all rows from the table
cursor.execute('DROP TABLE weather_data')
conn.commit()

# Close the database connection
conn.close()

print("All data has been cleared from the weather_data table.")
