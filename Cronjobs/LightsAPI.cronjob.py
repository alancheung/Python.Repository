'''
Send an API request to localhost LIFX controller and invoke the command.
'''
# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime
import argparse
import json
import requests

# ------------------------- DEFINE ARGUMENTS -------------------------
argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.add_argument("-r", "--request", required=True, help="JSON request to send.")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]
request = args["request"]

# ------------------------- DEFINE GLOBALS ---------------------------

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

def sendLightRequest(command):
    server = 'http://localhost:3000/api/lifx'
    try:
        log(f'Sending light request post to {server}')
        req = requests.post(f'{server}', data = command, timeout=30)
        if (req.status_code != 200):
            err(f"Request status code did not indicate success ({req.status_code})!");
    except Exception as ex:
        err(f"Could not send light request to '{server}' due to {str(ex)}!")
        successful = False

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    log("Run")
    parsedRequest = json.loads(request)

    log(f"Parsed {parsedRequest}")
    sendLightRequest(parsedRequest)
except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")