import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import statistics
import json
import argparse
import os

argParser = argparse.ArgumentParser()
argParser.add_argument("-o", "--output", default="calibration", help="The file name of the calibrated json.")
args = vars(argParser.parse_args())
outputFile = args["output"]

def percent(num, high, low):
    return 100 * (float(num - low) / float(high - low))

def calcValue(value):
    return percent(value, dryValue, wetValue)

def calcVoltage(voltage):
    return percent(voltage, dryVoltage, wetVoltage)

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Dry calibration
dryVal = []
dryVolt = []
skip = input("[DRY] calibration. Press 'S' to skip and Enter to begin...")
if (skip != "S"):
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
    dryValue = statistics.mean(dryVal)
    dryVoltage = statistics.mean(dryVolt)
    print(f"Dry Value Average: {dryValue}")
    print(f"Dry Voltage Average: {dryVoltage}")

# Wet calibration
wetVal = []
wetVolt = []
skip = input("[WET] calibration. Press 'S' to skip and Enter to begin...")
if (skip != "S"):
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
    wetValue = statistics.mean(wetVal)
    wetVoltage = statistics.mean(wetVolt)
    print(f"Wet Value Average: {wetValue}")
    print(f"Wet Voltage Average: {wetVoltage}")

# Continue the calibration and show computed values.
input("Note the values above. Press Enter to continue verification...")
if (len(wetVal) > 0 and len(dryVal) > 0):
    # Dump the settings to a file.
    calibratedObj = {
        "DryValue": dryValue,
        "DryVoltage": dryVoltage,
        "WetValue": wetValue,
        "WetVoltage": wetVoltage
        }
    fileName = f"./{outputFile}.json"
    if os.path.isfile(fileName):
        with open(fileName, "r+") as outputFile:
            data = outputFile.read()
            outputFile.seek(0)
            json.dump(calibratedObj, outputFile)
            outputFile.truncate()
    else:
        with open(fileName, "w") as outputFile:
            json.dump(calibratedObj, outputFile)
    print(f"Saved calibration values to {fileName}")

    print("Value\t\t\tVoltage")
    while True:
        rawVal = chan.value
        rawVolt = chan.voltage
        val = calcValue(rawVal)
        volt = calcVoltage(rawVolt)
        print(f"{rawVal} ({round(val, 4)}%)\t\t\t{rawVolt} ({round(volt, 4)}%)")
        time.sleep(0.5)
else:
    print("No calibration values to display.")
