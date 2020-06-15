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
import adafruit_ads1x15.ads1115 as ADS
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
argParser.add_argument("-l", "--location", default="Test", help="Location of the sensor")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]

wetThreshold = args["wet_threshold"]
dryThreshold = args["dry_threshold"]

location = args["location"]

# ------------------------- DEFINE GLOBALS ---------------------------
# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%H:%M:%S")
        message = f"{now}: {text}"
        if logFileName is not None:
            with open(f"{logFileName}", "a") as fout:
                fout.write(f"{message}\n")
        else:
            print(message)

def err(text):
    log(text, True)

def calculateVH400(voltage):
    '''
    Implementation of https://vegetronix.com/Products/VH400/VH400-Piecewise-Curve.phtml
    '''
    VWC = "Calculation failed!"
    if voltage <= 1.1:
        VWC = 10*voltage-1
    elif voltage > 1.1 and voltage <= 1.3:
        VWC = 25*voltage-17.5
    elif voltage > 1.3 and voltage <= 1.82:
        VWC = 48.08*voltage-47.5
    elif voltage > 1.82 and voltage <= 2.2:
        VWC = 26.32*voltage-7.89
    else: # Assuming voltage > 2.2
        VWC = 62.5*voltage - 87.5
    return VWC;

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    while True:
        rawVal = chan.value
        rawVoltage = chan.voltage
        waterContent = calculateVH400(rawVoltage)

        log(f'ADCValue: {rawVal}, Voltage: {rawVoltage}v, Moisture: {waterContent}%')
        time.sleep(1)
except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")