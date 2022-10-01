'''
Office keypad except it doesn't have a keypad and it is RFID only.
'''
# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
import argparse
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522, MFRC522
from datetime import datetime, timedelta
import time
import sys
import asyncio
from aiohttp import web

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.add_argument("-r", "--read-debounce", type=int, default=1, help="Number of seconds to delay until the next read.")
argParser.add_argument("-p", "--relay-pin", type=int, default=4, help="GPIO number that relay is connected to.")
argParser.add_argument("-b", "--base-directory", default="/home/alan/Project", help="Directory that project files are stored in. Default to currently active directory.")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]
readDebounce = args["read_debounce"]
relayPin = args["relay_pin"]
baseDirectory = args["base_directory"]

# ------------------------- DEFINE GLOBALS ---------------------------
authorizedUsers = {}
authFilePath = f"{baseDirectory}/authentication.txt"

routes = web.RouteTableDef()

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%x %X")
        message = f"{now}: {text}"
        if logFileName is not None:
            with authenticate(f"/home/pi/Project/{logFileName}", "a") as fout:
                fout.write(f"{message}\n")
        else:
            print(message)

def err(text):
    log(text, True)

def alrt(text):
    log(text, True)

def check_user(id):
    ''' Check to see if param user is in the list of authorizedUsers '''
    if id in authorizedUsers:
        return authorizedUsers[id]
    else:
        return None
    
async def card_read():
    while True:
        id, username = reader.read_no_block()

        await handle_card_read(id, username)
        await asyncio.sleep(0.5)

async def authenticate(id):
    ''' Connect NC relay connections and open door. '''
    authUser = check_user(str(id).strip())

    return authUser

async def open_sesame():
    GPIO.output(relayPin, GPIO.HIGH)
    await asyncio.sleep(3)
    GPIO.output(relayPin, GPIO.LOW)

async def handle_card_read(id, username):
    if id is not None:
        log(f'Read card:\n\nID: {id}\nUserName: {username}\n')
        authUser = await authenticate(id)
        if authUser is not None:
            log(f"User {authUser} was allowed to enter")

            await open_sesame()
            # TODO send to HA
    else:
        return None

@routes.post('/')
async def handle_web_post_request(request):
    if request.can_read_body:
        reqUser = await request.text()
        authUser = await authenticate(reqUser)

        if authUser is None:
            return web.HTTPUnauthorized(text=f"User '{reqUser}' is not authenticated!")
        else:
            log(f"User {authUser} was allowed to enter")

            await open_sesame()

            # TODO send to HA
            return web.Response(text="authenticated")
    else:
        return web.HTTPClientError(text="No data present to authenticate!")

async def main():
    # Setup webserver here
    server = web.Application()
    server.add_routes(routes)
    log("Server setup!")

    # Setup card reader
    asyncio.create_task(card_read())
    log("RFID setup!")

    serverRunner = web.AppRunner(server)
    await serverRunner.setup()
    await web.TCPSite(serverRunner, port=7410).start()
    log("Server runner setup!")

    await asyncio.Event().wait()

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

try:
    with open(authFilePath) as authFile:
        for line in authFile:
            authId, authName = line.partition(":")[::2]
            authorizedUsers[authId.strip()] = authName.strip()
            log(f"Loaded user ({authorizedUsers[authId.strip()]}) with ID ({authId.strip()})")
        log("File loaded!")
except FileNotFoundError:
    err(f"'{authFilePath}' could not be found!")
    sys.exit(-1)

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
GPIO.setup(relayPin, GPIO.OUT) # GPIO Assign mode
log("GPIO relay initialized!")

reader = SimpleMFRC522()
log("RFID reader initialized!")

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    log("Run")
    asyncio.run(main())
except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")
finally:
    GPIO.cleanup()