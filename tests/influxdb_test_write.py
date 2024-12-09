from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# InfluxDB connection details
token = "3I3Ur26_bYvoj9JCf9RoHC1qUgj7UO-3jAbbD5N1RMHzH_HLGHcJg9XKshtxoxjX_ioZ3bw3fEo7c3qA8bZ-8w=="
org = "BTP Project"
bucket = "Bucket 1"
url = "http://localhost:8086"

# Initialize InfluxDB client
client = InfluxDBClient(url=url, token=token, org=org)

# Create write API with synchronous write option
write_api = client.write_api(write_options=SYNCHRONOUS)

# Create a test data point
point = Point("environment") \
    .tag("location", "test_location") \
    .field("temperature", 25.3) \
    .field("humidity", 60.5) \
    .field("pressure", 1013.25) \
    .field("gas_resistance", 500) \
    .field("uv_data", 200) \
    .field("ambient_light", 300) \
    .time(datetime.utcnow())

try:
    # Write data point to InfluxDB
    write_api.write(bucket=bucket, org=org, record=point)
    print("Test data written to InfluxDB.")
except Exception as e:
    print(f"An error occurred while writing to InfluxDB: {e}")
finally:
    # Close the client
    client.close()
