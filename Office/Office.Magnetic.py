#!/usr/bin/python3

# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime, time, timedelta
from time import sleep
import json
import requests
import board
import adafruit_dht

import sys
import argparse
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument("-p", "--pin-sensor", type=int, default=26, help="BCM GPIO pin that sensor is connected to.")
argParser.add_argument("-o", "--open-time", type=int, default=15, help="Number of seconds since door open event to ignore lights off.")
argParser.add_argument("-r", "--reset-time", type=int, default=3, help="Workaround for intermittent sensor disconnects. Number of seconds to ignore close event.")
argParser.add_argument("-t", "--sensor-time", type=int, default=60, help="Number of seconds since last sensor before getting new temp/humidity data.")
argParser.add_argument("-s", "--server", default="", help="Server address to send log messages to")
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument('--debug', dest='debug', action='store_true', help="Disable light actions")
argParser.add_argument('--file', dest='file', action='store_true', help="Log to file instead of console.")

argParser.set_defaults(quiet=False)
argParser.set_defaults(debug=False)
argParser.set_defaults(file=False)

args = vars(argParser.parse_args())
sensorPin = args["pin_sensor"]
resetTime = args["reset_time"]
openTime = args["open_time"]
sensorTime = args["sensor_time"]
quiet = args["quiet"]
debug = args["debug"]
file = args["file"]
server = args["server"]

# ------------------------- DEFINE GLOBALS ---------------------------

global humidity
global temperature
temperature = None
humidity = None

isDoorOpen = False

lastOpen = None
lastClosed = None
lastSensor = None

lightConfigs = None
work_start = None
work_end = None
afternoon_dimmer = None

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%x %X")
        message = f"{now}: {text}"
        if file:
            with open("/home/pi/Project/sensor.log", "a") as fout:
                fout.write(f"{message}\n")
        else:
            print(message)

def err(text):
    log(text, True)

def cToF(temperature):
    fTemp = (temperature * (9/5)) + 32
    return fTemp

def sendSensorState(temp, humd, door):
    if server != "" and temp is not None and humd is not None and door is not None:
        try:
            log(f'Sending sensor request post to {server}')
            header = {'Authorization': 'Bearer ' + bearer}
            command = { "office_temperature": round(temp, 1), "office_humidity": humd, "office_door_state": door }
            
            log(f'Command was {command}')
            req = requests.post(f'{server}', json=command, headers=header, timeout=30)

            if (req.status_code != 200):
                err(f"Request status code did not indicate success ({req.status_code})!");
        except Exception as ex:
            err(f"Could not send sensor request to '{server}' due to {type(ex).__name__}!")
            successful = False

def handleOpen(temp, humd, door):
    log("Open:High")

    global lastOpen
    now = datetime.now()
    lastOpen = now

    sendSensorState(temp, humd, door)

def handleClose(temp, humd, door):
    log("Closed:Low")

    global lastClosed
    now = datetime.now()
    lastClosed = now

    sendSensorState(temp, humd, door)

def handleSensor(temp, humd, door):
    log("Sensor")

    global lastSensor
    now = datetime.now()
    lastSensor = now

    sendSensorState(temp, humd, door)

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet=True)

with open('/home/pi/Project/bearer.b') as f:
    bearer = f.read()

if (bearer is not None):
    log(f'Bearer initialized!')
else:
    err("'/home/pi/Project/bearer.b' could not be found!")
    sys.exit(-1)

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensorPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
log("GPIO initialized!")

isDoorOpen = GPIO.input(sensorPin)
if isDoorOpen:
    lastOpen = datetime.now()
    log("Door initialized as OPEN!")
else:
    lastClosed = datetime.now()
    log("Door initialized as CLOSED!")

dht = adafruit_dht.DHT22(board.D17)
lastSensor = datetime.now()

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    while True:
        try:
            lastState = isDoorOpen
            isDoorOpen = GPIO.input(sensorPin)

            if lastState != isDoorOpen:
                if(isDoorOpen):
                    handleOpen(cToF(temperature), humidity, isDoorOpen)
                else:
                    # listen for awhile to determine if this is a freak disconnect
                    freakDisconnect = False
                    start = datetime.now()
                    while freakDisconnect == False and (datetime.now() - start).seconds < resetTime:
                        isDoorOpen = GPIO.input(sensorPin)
                        freakDisconnect = isDoorOpen

                    # done listening, should I turn off lights?
                    if freakDisconnect == True:
                        log(f"Ignoring close event because of sensor reset in {(datetime.now() - start).seconds}s!", True)
                    else:
                        handleClose(cToF(temperature), humidity, isDoorOpen)
            if (datetime.now() - lastSensor).seconds > sensorTime:
                # Update sensor time before reading so that if the reading errors we don't spam the sensor.
                # Adds dependability on sensorTime > refresh rate (~2 seconds) for DHT22.
                lastSensor = datetime.now()
                
                humidity = dht.humidity
                temperature = dht.temperature
                log(f"Temp: {temperature}  //  Humd: {humidity}")
                handleSensor(cToF(temperature), humidity, isDoorOpen)
        except KeyboardInterrupt:
            raise
        except Exception as runEx:
            err(f"Unexpected exception during run, ignoring! {type(runEx).__name__}: {str(runEx)}")
except KeyboardInterrupt:
    err("KeyboardInterrupt caught!")
except Exception as ex:
    err(f"Unhandled exception ({type(ex).__name__}) caught! {str(ex)}")
finally:
    err("Cleaning up...")
    GPIO.cleanup()
    dht.exit()
    err("GPIO.cleanup() called!")