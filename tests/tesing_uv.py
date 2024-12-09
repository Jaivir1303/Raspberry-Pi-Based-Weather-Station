import time
from DFRobot_LTR390UV import DFRobot_LTR390UV_I2C
# Constants for measurement settings (copied from the DFRobot_LTR390UV library)
e20bit = 0  # 20-bit data
e19bit = 16 # 19-bit data
e18bit = 32 # 18-bit data
e17bit = 48 # 17-bit data
e16bit = 64 # 16-bit data
e13bit = 80 # 13-bit data

e25ms = 0   # Sampling time of 25ms
e50ms = 1   # Sampling time of 50ms
e100ms = 2  # Sampling time of 100ms
e200ms = 3  # Sampling time of 200ms
e500ms = 4  # Sampling time of 500ms
e1000ms = 5 # Sampling time of 1000ms
e2000ms = 6 # Sampling time of 2000ms

# Constants for gain settings (from the DFRobot_LTR390UV library)
eGain1 = 0  # Gain of 1
eGain3 = 1  # Gain of 3
eGain6 = 2  # Gain of 6
eGain9 = 3  # Gain of 9
eGain18 = 4 # Gain of 18


# Define I2C bus and device address (0x1C as per your setup)
i2c_bus = 1  # Typically, I2C bus 1 is used on Raspberry Pi
ltr390_address = 0x1C

# Initialize the sensor
ltr390 = DFRobot_LTR390UV_I2C(i2c_bus, ltr390_address)

# Begin sensor operation and check if initialization is successful
if not ltr390.begin():
    print("Failed to initialize LTR390UV sensor")
else:
    print("LTR390UV sensor initialized successfully")

# Set the sensor to UVS mode (for UV detection)
ltr390.set_mode(0x0A)  # UVS mode as per the library

# Set measurement rate and gain
ltr390.set_ALS_or_UVS_meas_rate(e18bit, e100ms)  # 18-bit resolution and 100ms sampling
ltr390.set_ALS_or_UVS_gain(eGain3)  # Set gain to 3 (default)

# Read UVS data in a loop
try:
    while True:
        uvs_data = ltr390.read_original_data()
        print(f"UVS Data: {uvs_data}")
        time.sleep(1)  # Read every 1 second
except KeyboardInterrupt:
    print("Measurement stopped.")
