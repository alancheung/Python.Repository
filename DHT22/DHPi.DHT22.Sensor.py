# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime
import argparse
import time
import adafruit_dht
import board
import json
import requests
import socket
import sys

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-s", "--server", default="", help="Server address to send log messages to")
argParser.add_argument("-l", "--location", default="", help="Location of the sensor")
argParser.add_argument("-m", "--manufacturer", default="HiLetGo", help="DHT22 manufacturer")
argParser.add_argument("-p", "--pin", type=int, default=17, help="Board GPIO pin that sensor is connected to.")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
server = args["server"]
location = args["location"]
manufacturer = args["manufacturer"]
sensorPin = args["pin"]

# ------------------------- DEFINE GLOBALS ---------------------------

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%H:%M:%S")
        message = f"{now}: {text}"
        print(message)

def err(text):
    log(text, True)

def cToF(temperature):
    fTemp = (temperature * (9/5)) + 32
    return fTemp


def sendToServer(temperature, humidity):
    successful = True
    if server != "":
        try:
            tempReading = { "SourceHostName": socket.gethostname(), "Location": location, "SensorModel": f"{manufacturer} DHT22", "ReadingType": "Temperature", "ReadingValue": temperature  }
            log(f'Sending temperature post to {server}')
            req = requests.post(server, data = tempReading, timeout=30)
            if (req.status_code != 200):
                raise ConnectionError(f"Request status code did not indicate success ({req.status_code})!");
        except Exception as ex:
            err(f"Could not send temperature to '{server}' due to {type(ex).__name__}!")
            successful = False

        try:
            humidityReading = { "SourceHostName": socket.gethostname(), "Location": location, "SensorModel": f"{manufacturer} DHT22", "ReadingType": "Humidity", "ReadingValue": humidity  }
            log(f'Sending temperature post to {server}')
            req = requests.post(server, data = humidityReading, timeout=30)
            if (req.status_code != 200):
                raise ConnectionError(f"Request status code did not indicate success ({req.status_code})!");
        except Exception as ex:
            err(f"Could not send humidity to '{server}' due to {type(ex).__name__}: {str(ex)}!")
            successful = False
    return successful

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

dht = adafruit_dht.DHT22(sensorPin)

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    sent = False
    while not sent:
        try:
            humidity = dht.humidity
            temperature = cToF(dht.temperature)

            # Print what we got to the REPL
            log("Temp: {:.1f} *C \t Humidity: {}%".format(temperature, humidity), True)
            sendToServer(temperature, humidity)
            sent = True
        except RuntimeError as e:
            # Reading doesn't always work! Just print error and we'll try again
            print("Reading from DHT failure: ", e.args)
        time.sleep(1)
except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")