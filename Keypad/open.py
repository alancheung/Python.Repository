
'''
Simple open program with no authentication
'''
# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime
import argparse
import PySimpleGUI as sg
import time
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
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.add_argument("-p", "--relay-pin", type=int, default=4, help="GPIO number that sensor is connected to.")
argParser.add_argument("-o", "--open-time", type=int, default=3, help="Number of seconds to keep relay open (and lock unlocked).")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]
relayPin = args["relay_pin"]
openTime = args["open_time"]

# ------------------------- DEFINE GLOBALS ---------------------------

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

def alrt(text):
    log(text, True)

def open_sesame():
    window[passwordKey].update('ACCESS GRANTED')
    
    # Connect NC relay connections and open door.
    GPIO.output(relayPin, GPIO.HIGH)
    time.sleep(openTime)
    GPIO.output(relayPin, GPIO.LOW)

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

layout = [[sg.Submit('OPEN', size=(600, 460))]]
log("GUI layout set!")

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
GPIO.setup(relayPin, GPIO.OUT) # GPIO Assign mode
log("GPIO initialized!")

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    showKeypad = True
    #, no_titlebar=True, location=(0,0), size=piTouchSize, keep_on_top=True
    window = sg.Window('Error', layout, no_titlebar=True, location=(0,0), size=(800, 480), keep_on_top=False).Finalize()

    while showKeypad:
        event, values = window.read()
        log(event)

        if event in ('Submit', 'OPEN'):
            open_sesame()

        # This captures the Ctrl-C and exit button events
        elif event in (sg.WIN_CLOSED, 'Quit'):
            #sg.popup("Closing")
            break

except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")
finally:
    GPIO.cleanup()
    log("Program exiting...")