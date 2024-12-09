
import time
import sqlite3
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import random
import json
import argparse
import os

# Configuration
SQLITE_DB_PATH = '/home/jaivir1303/myproject/RaspberryPi-Weather-Station/project/tests/weather_data.db'
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')  # Replace with your token
INFLUXDB_ORG = "BTP Project"
INFLUXDB_BUCKET = "Weather Data"
TOTAL_RECORDS = 5400  # 90 minutes * 60 seconds
BATCH_SIZE = 100  # Number of records per batch

def generate_dummy_data(num_records):
    data = []
    for _ in range(num_records):
        record = {
            "temperature": round(random.uniform(15.0, 35.0), 2),
            "humidity": round(random.uniform(30.0, 90.0), 2),
            "pressure": round(random.uniform(980.0, 1050.0), 2),
            "ambient_light": round(random.uniform(100.0, 1000.0), 2),
            "uv": round(random.uniform(0.0, 11.0), 2),
            "gas_resistance": round(random.uniform(10000.0, 20000.0), 2)
        }
        data.append(record)
    return data

def write_sqlite(cursor, data):
    start_time = time.time()
    cursor.executemany('''
        INSERT INTO weather (temperature, humidity, pressure, ambient_light, uv, gas_resistance)
        VALUES (:temperature, :humidity, :pressure, :ambient_light, :uv, :gas_resistance)
    ''', data)
    return time.time() - start_time

def write_influx(write_api, data):
    start_time = time.time()
    points = []
    for record in data:
        point = Point("weather") \
            .field("temperature", record["temperature"]) \
            .field("humidity", record["humidity"]) \
            .field("pressure", record["pressure"]) \
            .field("ambient_light", record["ambient_light"]) \
            .field("uv", record["uv"]) \
            .field("gas_resistance", record["gas_resistance"]) \
            .time(time.time_ns(), WritePrecision.NS)
        points.append(point)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
    return time.time() - start_time

def main():
    parser = argparse.ArgumentParser(description="Write Performance Test")
    parser.add_argument('--total', type=int, default=TOTAL_RECORDS, help='Total number of records to write')
    parser.add_argument('--batch', type=int, default=BATCH_SIZE, help='Number of records per batch')
    args = parser.parse_args()

    total_records = args.total
    batch_size = args.batch

    # Generate dummy data
    data = generate_dummy_data(total_records)

    # Setup SQLite connection
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    # Setup InfluxDB client
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Initialize metrics
    sqlite_times = []
    influx_times = []

    # Write data in batches
    for i in range(0, total_records, batch_size):
        batch = data[i:i+batch_size]

        # Write to SQLite
        sqlite_time = write_sqlite(cursor, batch)
        sqlite_times.append(sqlite_time)

        # Write to InfluxDB
        influx_time = write_influx(write_api, batch)
        influx_times.append(influx_time)

        print(f"Batch {i//batch_size +1}: SQLite Write Time = {sqlite_time:.4f}s, InfluxDB Write Time = {influx_time:.4f}s")

    # Commit SQLite transactions
    conn.commit()
    conn.close()
    client.close()

    # Calculate metrics
    total_sqlite_time = sum(sqlite_times)
    total_influx_time = sum(influx_times)
    avg_sqlite_time = total_sqlite_time / len(sqlite_times)
    avg_influx_time = total_influx_time / len(influx_times)

    print("\nWrite Performance Metrics:")
    print(f"Total SQLite Write Time: {total_sqlite_time:.4f}s")
    print(f"Average SQLite Write Time per Batch: {avg_sqlite_time:.4f}s")
    print(f"Total InfluxDB Write Time: {total_influx_time:.4f}s")
    print(f"Average InfluxDB Write Time per Batch: {avg_influx_time:.4f}s")

    # Save metrics to a JSON file
    metrics = {
        "sqlite": {
            "total_time_sec": total_sqlite_time,
            "average_time_per_batch_sec": avg_sqlite_time,
            "batches": len(sqlite_times)
        },
        "influxdb": {
            "total_time_sec": total_influx_time,
            "average_time_per_batch_sec": avg_influx_time,
            "batches": len(influx_times)
        }
    }

    with open("write_performance_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    print("\nWrite performance metrics saved to write_performance_metrics.json")

if __name__ == "__main__":
    main()
