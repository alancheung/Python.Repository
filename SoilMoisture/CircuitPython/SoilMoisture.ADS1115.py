# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime
import argparse
import requests
import socket
import statistics
import sys
import os
import json
import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.add_argument("-w", "--wet-threshold", type=int, default=15, help="The value at which the soil is considered excessively wet.")
argParser.add_argument("-d", "--dry-threshold", type=int, default=75, help="The value at which the soil is considered excessively dry.")
argParser.add_argument("-l", "--location", default=None, help="Location of the sensor", required=True)
argParser.add_argument("-s", "--server", default="", help="Server address to send log messages to")
argParser.add_argument("-m", "--manufacturer", default="Gikfun", help="Manufacturer of the sensor")
argParser.set_defaults(quiet=False)

# DryValue: 22528; DryVoltage: 2.812 // WetValue: 10477; WetVoltage: 1.309
args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]

wetThreshold = args["wet_threshold"]
dryThreshold = args["dry_threshold"]

server = args["server"]
location = args["location"]
manufacturer = args["manufacturer"]

# ------------------------- DEFINE GLOBALS ---------------------------
# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Calibration values
calibration = None
dryValue = None
dryVoltage = None
wetValue = None
wetVoltage = None

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%H:%M:%S")
        message = f"{now}: {text}"
        if logFileName is not None:
            with open(f"/home/pi/Project/{logFileName}", "a") as fout:
                fout.write(f"{message}\n")
        else:
            print(message)

def err(text):
    log(text, True)
    
def percent(num, high, low):
    return 100 * (float(num - low) / float(high - low))

def calcValue(value):
    return 100 - percent(value, dryValue, wetValue)

def calcVoltage(voltage):
    return 100 - percent(voltage, dryVoltage, wetVoltage)

def sendToServer(name, value):
    successful = True
    if server != "":
        try:
            tempReading = { 
                "SourceHostName": socket.gethostname(), 
                "Location": location, 
                "SensorModel": f"{manufacturer} EK1940", 
                "ReadingType": name, 
                "ReadingValue": value
            }
            log(f'Sending {name} reading post to {server}')
            req = requests.post(server, data = tempReading, timeout=30)
            if (req.status_code != 200):
                raise ConnectionError(f"Request status code did not indicate success ({req.status_code})!");
        except Exception as ex:
            err(f"Could not send {name} reading to '{server}' due to {type(ex).__name__}! {str(ex)}")
            successful = False
    return successful


# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

try:
    with open("/home/pi/Project/calibration.json") as timestoneFile:
        calibration = json.load(timestoneFile)
        log("File loaded!")
except FileNotFoundError:
    err("'/home/pi/Project/calibration.json' could not be found!")
    sys.exit(-1)
log(f"Calibration: {calibration}", displayWhenQuiet=True)
dryValue = calibration["DryValue"]
dryVoltage = calibration["DryVoltage"]
wetValue = calibration["WetValue"]
wetVoltage = calibration["WetVoltage"]

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    print(f"Value\tVoltage")
    rawVal = chan.value
    rawVoltage = chan.voltage
    val = calcValue(rawVal)
    volt = calcVoltage(rawVoltage)

    # If one is dry and the other is wet then maybe retest sensor?
    if (val >= dryThreshold and volt <= wetThreshold) or (val <= wetThreshold and volt >= dryThreshold):
        err(f"Sensor mismatch! RawADC:{rawVal}/({dryValue}-{wetValue}) vs Voltage{rawVoltage}/({dryVoltage}-{wetVoltage})")
    else:
        avg = statistics.mean([val, volt])
        log(f'ADCValue: {rawVal}, Voltage: {rawVoltage}v, Moisture: {avg}%')
        sendToServer("Moisture", avg)
        sendToServer("ADCValue", rawVal)
        sendToServer("Voltage", rawVoltage)
except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")