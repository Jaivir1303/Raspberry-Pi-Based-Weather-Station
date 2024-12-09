import time
import sqlite3
from influxdb_client import InfluxDBClient
import argparse
import json
import os
# Configuration
SQLITE_DB_PATH = '/home/jaivir1303/myproject/RaspberryPi-Weather-Station/project/tests/weather_data.db'
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')  # Replace with your actual InfluxDB token
INFLUXDB_ORG = "BTP Project"
INFLUXDB_BUCKET = "Weather Data"

def setup_sqlite_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

def setup_influxdb_client():
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    return client

def list_influxdb_measurements_and_fields(client):
    query = '''
    import "influxdata/influxdb/schema"

    // List all measurements
    schema.measurements(bucket: "Weather Data")
    '''

    query_api = client.query_api()
    measurements = []
    try:
        tables = query_api.query(query, org=INFLUXDB_ORG)
        for table in tables:
            for record in table.records:
                measurements.append(record.get_value())
    except Exception as e:
        print(f"Error listing measurements: {e}")
        return {}

    measurement_fields = {}
    for measurement in measurements:
        # Now list fields for each measurement using 'schema.fieldKeys' with predicate
        field_query = f'''
        import "influxdata/influxdb/schema"

        schema.fieldKeys(
          bucket: "Weather Data",
          predicate: (r) => r["_measurement"] == "{measurement}"
        )
        '''
        try:
            field_tables = query_api.query(field_query, org=INFLUXDB_ORG)
            fields = []
            for table in field_tables:
                for record in table.records:
                    fields.append(record.get_value())
            measurement_fields[measurement] = fields
        except Exception as e:
            print(f"Error listing fields for measurement {measurement}: {e}")
    
    return measurement_fields

def perform_sqlite_queries(cursor):
    queries = {
        "average_temperature": "SELECT AVG(temperature) FROM weather",
        "max_humidity": "SELECT MAX(humidity) FROM weather",
        "min_pressure": "SELECT MIN(pressure) FROM weather",
        "average_uv": "SELECT AVG(uv) FROM weather",
        "max_gas_resistance": "SELECT MAX(gas_resistance) FROM weather"
    }
    results = {}
    for name, query in queries.items():
        start_time = time.time()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        end_time = time.time()
        results[name] = {
            "result": result,
            "time_sec": end_time - start_time
        }
    return results

def perform_influxdb_queries(client, measurement, available_fields):
    # Define the desired queries based on available fields
    queries = {}
    if "temperature" in available_fields:
        queries["average_temperature"] = f'''
from(bucket:"Weather Data")
  |> range(start: -90m)
  |> filter(fn: (r) => r["_measurement"] == "{measurement}" and r["_field"] == "temperature")
  |> mean(column:"_value")
'''
    else:
        print("Field 'temperature' not found in InfluxDB measurement.")

    if "humidity" in available_fields:
        queries["max_humidity"] = f'''
from(bucket:"Weather Data")
  |> range(start: -90m)
  |> filter(fn: (r) => r["_measurement"] == "{measurement}" and r["_field"] == "humidity")
  |> max(column:"_value")
'''
    else:
        print("Field 'humidity' not found in InfluxDB measurement.")

    if "pressure" in available_fields:
        queries["min_pressure"] = f'''
from(bucket:"Weather Data")
  |> range(start: -90m)
  |> filter(fn: (r) => r["_measurement"] == "{measurement}" and r["_field"] == "pressure")
  |> min(column:"_value")
'''
    else:
        print("Field 'pressure' not found in InfluxDB measurement.")

    if "uv" in available_fields:
        queries["average_uv"] = f'''
from(bucket:"Weather Data")
  |> range(start: -90m)
  |> filter(fn: (r) => r["_measurement"] == "{measurement}" and r["_field"] == "uv")
  |> mean(column:"_value")
'''
    else:
        print("Field 'uv' not found in InfluxDB measurement.")

    if "gas_resistance" in available_fields:
        queries["max_gas_resistance"] = f'''
from(bucket:"Weather Data")
  |> range(start: -90m)
  |> filter(fn: (r) => r["_measurement"] == "{measurement}" and r["_field"] == "gas_resistance")
  |> max(column:"_value")
'''
    else:
        print("Field 'gas_resistance' not found in InfluxDB measurement.")

    results = {}
    query_api = client.query_api()
    for name, query in queries.items():
        start_time = time.time()
        try:
            tables = query_api.query(query, org=INFLUXDB_ORG)
            # Extract the result
            value = None
            for table in tables:
                for record in table.records:
                    value = record.get_value()
            end_time = time.time()
            results[name] = {
                "result": value,
                "time_sec": end_time - start_time
            }
        except Exception as e:
            print(f"Error performing query '{name}': {e}")
            results[name] = {
                "result": None,
                "time_sec": None,
                "error": str(e)
            }
    return results

def main():
    parser = argparse.ArgumentParser(description="Read Performance Test")
    args = parser.parse_args()

    # Setup connections
    conn, cursor = setup_sqlite_connection()
    influx_client = setup_influxdb_client()

    # List available measurements and fields
    print("Listing available measurements and fields in InfluxDB:")
    measurement_fields = list_influxdb_measurements_and_fields(influx_client)
    for measurement, fields in measurement_fields.items():
        print(f"Measurement: {measurement}")
        print(f"  Fields: {', '.join(fields)}")

    # Choose the measurement to query
    if "weather" not in measurement_fields:
        print("Measurement 'weather' not found in InfluxDB.")
        influx_client.close()
        conn.close()
        return
    else:
        available_fields = measurement_fields["weather"]
        print(f"\nAvailable fields in 'weather' measurement: {', '.join(available_fields)}")

    # Perform SQLite queries
    sqlite_results = perform_sqlite_queries(cursor)

    # Perform InfluxDB queries
    influx_results = perform_influxdb_queries(influx_client, "weather", available_fields)

    # Close connections
    conn.close()
    influx_client.close()

    # Print results
    print("\nRead Performance Metrics:")
    print("SQLite:")
    for key, value in sqlite_results.items():
        print(f"  {key}: {value['result']} (Time: {value['time_sec']:.6f}s)")

    print("\nInfluxDB:")
    for key, value in influx_results.items():
        if 'error' in value:
            print(f"  {key}: Error: {value['error']} (Time: N/A)")
        else:
            print(f"  {key}: {value['result']} (Time: {value['time_sec']:.6f}s)")

    # Save metrics to a JSON file
    metrics = {
        "sqlite": sqlite_results,
        "influxdb": influx_results
    }

    with open("read_performance_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    print("\nRead performance metrics saved to read_performance_metrics.json")

if __name__ == "__main__":
    main()
