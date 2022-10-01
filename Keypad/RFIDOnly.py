'''
Office keypad except it doesn't have a keypad and it is RFID only.
'''
# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime
import argparse
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from datetime import datetime, time, timedelta

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.add_argument("-r", "--read-debounce", type=int, default=1, help="Number of seconds to delay until the next read.")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]
readDebounce = args["read_debounce"]

# ------------------------- DEFINE GLOBALS ---------------------------
lastRead = datetime.now()

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%x %X")
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

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)
reader = SimpleMFRC522()

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    log("Run")
    while True:
        if (datetime.now() - lastRead).seconds >= readDebounce:
            id, username = reader.read()
            lastRead = datetime.now()
            log(f'Read card:\n\nID: {id}\nUserName: {username}')
except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")
finally:
        GPIO.cleanup()