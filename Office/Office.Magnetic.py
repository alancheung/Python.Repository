#!/usr/bin/python3

# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime, time, timedelta
from time import sleep
import json
import requests

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
argParser.add_argument("-p", "--pin-sensor", type=int, default=37, help="Board GPIO pin that sensor is connected to.")
argParser.add_argument("-o", "--open-time", type=int, default=15, help="Number of seconds since door open event to ignore lights off.")
argParser.add_argument("-r", "--reset-time", type=int, default=3, help="Workaround for intermittent sensor disconnects. Number of seconds to ignore close event.")
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
quiet = args["quiet"]
debug = args["debug"]
file = args["file"]
server = args["server"]

# ------------------------- DEFINE GLOBALS ---------------------------

isDoorOpen = False
lastOpen = None
lastClosed = None

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

def is_between_time(time_to_check, start, end):
    if start > end:
        if time_to_check >= start or time_to_check < end:
            return True
    elif start < end:
        if time_to_check >= start and time_to_check < end:
            return True
    elif time_to_check == start:
        return True
    return False

def convert_time(timestring):
    return datetime.strptime(timestring, "%H:%M").time()

def get_light_sequence(now):
    # Get the first config where 
    #       the current time is between the start and end 
    #       the current day is not excluded
    config = next((c for c in lightConfigs if is_between_time(now, convert_time(c["StartTime"]), convert_time(c["EndTime"])) and (0 in c["ExcludedDays"]) == False), None)

    if config is None:
        err("Could not find a valid light sequence at {now.strftime('%x %X')}!")
    else:
        log(f"Found config at {now.strftime('%x %X')} with description {config['Description']}")
    return config

def lightOnSequence():
    if debug: return
    now = datetime.now()

    lightSequence = get_light_sequence(now)
    if lightSequence is None:
        # Give a default sequence if nothing is found.
        lightSequence = [
            {
                "LifxCommandType": "COLOR",
                "Lights": [ "Office One", "Office Two", "Office Three", "Desk Strip" ],
                "TurnOn": "true",
                "Duration": 10000,
                "Color": "white",
                "Brightness": 1.0,
                "Kelvin": 2500,
            }]
    
    sequence = { "Count": 1, "Sequence": lightSequence }
    sendLightRequest('api/lifx/sequence', sequence)

def lightOffSequence():
    if debug: return

    lightOff = {
        "LifxCommandType": "OFF",
	    "Lights": ["Office One", "Office Two", "Office Three", "Desk Strip"],
	    "Duration": 1000
    }
    sendLightRequest('api/lifx', lightOff)

def sendAccessLog(state):
    if server != "":
        try:
            log(f'Sending access log post to {server}')
            event = { "Name": "OfficeDoor", "State": state }
            req = requests.post(f'{server}/api/portal', data = event)
            if (req.status_code != 200):
                err(f"Request status code did not indicate success ({req.status_code})!");
        except Exception as ex:
            err(f"Could not send log to remote due to {type(ex).__name__}!")

def sendLightRequest(url, command):
    if server != "":
        try:
            log(f'Sending light request post to {server}')
            req = requests.post(f'{server}/{url}', json = command, timeout=30)
            if (req.status_code != 200):
                err(f"Request status code did not indicate success ({req.status_code})!");
        except Exception as ex:
            err(f"Could not send light request to '{server}' due to {type(ex).__name__}!")
            successful = False

def handleOpen():
    log("Open:High")
    sendAccessLog(True)
    now = datetime.now()

    global lastOpen
    lastOpen = now

    log("Turn on lights!", True)
    lightOnSequence()

def handleClose():
    log("Closed:Low")
    sendAccessLog(False)
    now = datetime.now()

    global lastClosed
    lastClosed = now

    timeSinceOpen = now - lastOpen
    if timeSinceOpen.seconds > openTime:
        # Some time has passed since the door opened, turn off lights
        log("Turn off lights!", True)
        lightOffSequence()
    else:
        log(f"Not enough time ({timeSinceOpen.seconds}s) has passed to take action on CLOSE event.", True)

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet=True)

try:
    with open("/home/pi/Project/light-config.json") as configFile:
        lightConfigs = json.load(configFile)
        log("File loaded!")
except FileNotFoundError:
    err("'/home/pi/Project/light-config.json' could not be found!")
    sys.exit(-1)

log(f"light-config: {lightConfigs}", displayWhenQuiet=True)
log("Light Config Loaded!")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(sensorPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
log("GPIO initialized!")

isDoorOpen = GPIO.input(sensorPin)
if isDoorOpen:
    lastOpen = datetime.now()
    log("Door initialized as OPEN!")
else:
    lastClosed = datetime.now()
    log("Door initialized as CLOSED!")

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
                    handleOpen()
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
                        handleClose()
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
    err("GPIO.cleanup() called!")