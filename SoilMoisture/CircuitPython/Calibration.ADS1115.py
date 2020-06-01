import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import statistics

def percent(num, high, low):
    return 100 * float(num - low) / float(high - low)

def calcValue(value):
    return percent(value, dryValue, wetValue)

def calcVoltage(voltage):
    return percent(voltage, dryVoltage, wetVoltage)

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Dry calibration
dryVal = []
dryVolt = []
input("[DRY] calibration. Press Enter to begin...")
print("{:>5}\t{:>5}".format('raw', 'v'))
while True:
    val = chan.value
    volt = chan.voltage
    print("{:>5}\t{:>5.3f}".format(val, volt))
    dryVal.append(val)
    dryVolt.append(volt)
    time.sleep(0.5)
    if len(dryVal) >= 30:
        break;

print(f"Dry Value Average: {statistics.mean(dryVal)}")
print(f"Dry Voltage Average: {statistics.mean(dryVolt)}")

# Wet calibration
wetVal = []
wetVolt = []
input("[WET] calibration. Press Enter to begin...")
print("{:>5}\t{:>5}".format('raw', 'v'))
while True:
    val = chan.value
    volt = chan.voltage
    print("{:>5}\t{:>5.3f}".format(val, volt))
    wetVal.append(val)
    wetVolt.append(volt)
    time.sleep(0.5)
    if len(wetVal) >= 30:
        break;


dryValue = statistics.mean(dryVal)
dryVoltage = statistics.mean(dryVolt)
wetValue = statistics.mean(wetVal)
wetVoltage = statistics.mean(wetVolt)
print(f"Dry Value Average: {dryValue}")
print(f"Dry Voltage Average: {dryVoltage}")
print(f"Wet Value Average: {wetValue}")
print(f"Wet Voltage Average: {statistics.mean(wetVolt)}")

input("Note the values above. Press Enter to continue verification...")
print("Value\tVoltage")
while True:
        val = calcValue(chan.value)
        volt = calcVoltage(chan.voltage)
        print(f"{val}\t{volt}")
        time.sleep(0.5)
