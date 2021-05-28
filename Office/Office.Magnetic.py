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

timestones = None
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

def is_between_time(time, time_range):
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]

def convert_time(timestring):
    return datetime.strptime(timestring, "%H:%M").time()

def lightOnSequence():
    if debug: return
    now = datetime.now()

    # If we're in the office for work then set correct color
    # Weekday Monday(0) - Sunday(6)
    if now.weekday() < 5 and is_between_time(now.time(), (work_start, work_end)):
        # Ignore Office One because Kelly.
        lightOn = [{
            # Need to turn on the strip in order to send commands. Turn on-set brightness to 0.
            "Lights": ["Desk Strip"],
            "TurnOn": "true",
            "ApplyZoneImmediately": "true",
            "Duration": 0,
            "Hue": 0.88,
            "Saturation": 0.0,
            "Brightness": 0.0,
            "Kelvin": 2500,
            "Delay": 0
        }, { # 1st Wave: Zones 4-7 & Office Two
	        "Lights": ["Desk Strip"],
            "Zones": [4, 7],
            "ApplyZoneImmediately": "true",
	        "Duration": 10000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": 1.0,
	        "Kelvin": 5500,
            "Delay": 0
        }, {
	        "Lights": ["Office Two"],
	        "TurnOn": "true",
	        "Duration": 10000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": 1.0,
	        "Kelvin": 5500,
            "Delay": 2000
        }, { # 2nd Wave: Zones 0-15 & Office Three
	        "Lights": ["Desk Strip"],
            "Zones": [0, 15],
            "ApplyZoneImmediately": "true",
	        "Duration": 8000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": 1.0,
	        "Kelvin": 5500,
            "Delay": 0
        }, {
	        "Lights": ["Office Three"],
	        "TurnOn": "true",
	        "Duration": 8000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": 1.0,
	        "Kelvin": 5500,
            "Delay": 1000
        }]
    else:
        if now.time() <= afternoon_dimmer:
            brightness = 1
        else:
            brightness = 0.45

        lightOn = [{
            # Need to turn on the strip in order to send commands. Turn on-set brightness to 0.
            "Lights": ["Desk Strip"],
            "TurnOn": "true",
            "ApplyZoneImmediately": "true",
            "Duration": 0,
            "Hue": 0.88,
            "Saturation": 0.0,
            "Brightness": 0.0,
            "Kelvin": 2500,
            "Delay": 0
        }, { # 1st Wave: Zones 5-10 & Office One
	        "Lights": ["Desk Strip"],
            "Zones": [5, 5],
            "ApplyZoneImmediately": "true",
	        "Duration": 10000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
            "Delay": 0
        }, {
	        "Lights": ["Office One"],
	        "TurnOn": "true",
	        "Duration": 10000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
            "Delay": 2000
        }, { # 2nd Wave: Zones 2-13 (overwriting previous zones) & Office Two
	        "Lights": ["Desk Strip"],
            "Zones": [2, 11],
            "ApplyZoneImmediately": "true",
	        "Duration": 8000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
            "Delay": 0
        }, {
	        "Lights": ["Office Two"],
	        "TurnOn": "true",
	        "Duration": 8000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
            "Delay": 1000
        }, { # 3rd Wave: Zones 0-15 (full strip, overwriting previous) & Office Three
	        "Lights": ["Desk Strip"],
            "Zones": [0, 15],
            "ApplyZoneImmediately": "true",
	        "Duration": 7000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
            "Delay": 0
        }, {
	        "Lights": ["Office Three"],
	        "TurnOn": "true",
	        "Duration": 7000,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
            "Delay": 7000
        }, { # 4th Wave: Flash Desk Strip Green
	        "Lights": ["Desk Strip"],
            "Zones": [0, 15],
            "ApplyZoneImmediately": "true",
	        "Duration": 500,
	        "Hue": 0.33333,
            "Saturation": 1.0,
            "Brightness": brightness,
            "Kelvin": 5500,
            "Delay": 1000
        }, {
	        "Lights": ["Desk Strip"],
            "Zones": [0, 15],
            "ApplyZoneImmediately": "true",
	        "Duration": 500,
	        "Hue": 0.88,
	        "Saturation": 0.0,
	        "Brightness": brightness,
	        "Kelvin": 2500,
        }]

    sequence = { "Count": 1, "Sequence": lightOn }
    sendLightRequest('api/lifx/sequence', lightOn)

def lightOffSequence():
    if debug: return

    lightOff = {
	    "Lights": ["Office One", "Office Two", "Office Three", "Desk Strip"],
	    "TurnOff": "true",
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
    with open("/home/pi/Project/timestones.json") as timestoneFile:
        timestones = json.load(timestoneFile)
        log("File loaded!")
except FileNotFoundError:
    err("'/home/pi/Project/timestones.json' could not be found!")
    sys.exit(-1)
log(f"Timestones: {timestones}", displayWhenQuiet=True)

work_start = convert_time(timestones["work_start"])
work_end = convert_time(timestones["work_end"])
afternoon_dimmer = convert_time(timestones["afternoon_dimmer"])
log("timestones converted!")

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