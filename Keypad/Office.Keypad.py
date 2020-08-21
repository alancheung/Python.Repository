'''
This module uses OpenCV and plain Python libraries to mimic a smart lock entry.
In addition to the traditional keypad setup, this module will use facial recognition
to determine valid users.
'''
# ------------------------- DEFINE IMPORTS ---------------------------
from __future__ import print_function
from datetime import datetime
import argparse
import PySimpleGUI as sg
import hashlib, binascii, os

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]

# ------------------------- DEFINE GLOBALS ---------------------------
passwordKey = '-PASSSWORD-'
passwordPrompt = 'Enter your password'
currentPassword = ''

globalPasswordHash = ''

# Layout sizes
piTouchWidth = 80
piTouchHeight = 40
piTouchSize = (piTouchWidth, piTouchHeight)

numButtonSize = (15, 10)


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

def update_password_count():
    '''
    Update the header with the appropriate number of * characters representing the length of the password entered.
    '''
    window[passwordKey].update('*' * len(currentPassword))

def hash_password(password):
    '''Hash a password for storing.'''
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    '''Verify a stored password against one provided by user'''
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def authenticate(tepidPassword):
    ok = verify_password('', tepidPassword)
    # TODO: DO STUFF HERE
    log(ok)
    return ok

def clear_password():
    global currentPassword

    currentPassword = ''
    update_password_count()

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

keypadLayout = [[sg.Text(passwordPrompt, key=passwordKey, size=(piTouchWidth, 5))],
                [sg.Button('7', size=numButtonSize), sg.Button('8', size=numButtonSize), sg.Button('9', size=numButtonSize)],
                [sg.Button('4', size=numButtonSize), sg.Button('5', size=numButtonSize), sg.Button('6', size=numButtonSize)],
                [sg.Button('1', size=numButtonSize), sg.Button('2', size=numButtonSize), sg.Button('3', size=numButtonSize)],
                [sg.Button('Clear', size=numButtonSize), sg.Button('0', size=numButtonSize), sg.Button('Face', size=numButtonSize)],
                [sg.Button('Submit', size=(piTouchWidth, 5))]]

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    showKeypad = True
    #, no_titlebar=True, location=(0,0), size=piTouchSize, keep_on_top=True
    window = sg.Window('Keypad', keypadLayout)

    while showKeypad:
        event, values = window.read()
        print(event)

        if (str(event).isnumeric()):
            currentPassword += str(event)
            update_password_count()

        elif event == 'Clear':
            clear_password()

        elif event == 'Face':
            print(hash_password(currentPassword))
            clear_password()

        elif event == 'Submit':
            authenticate(currentPassword)
            clear_password()

        if event in (sg.WIN_CLOSED, 'Quit'):
            sg.popup("Closing")
            break

except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")