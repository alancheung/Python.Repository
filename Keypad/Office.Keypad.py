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
import scrypt
import os

# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
#argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
#argParser.add_argument("-s", "--salt", default=None, help="Unique salt for this program", required=True)
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]

# ------------------------- DEFINE GLOBALS ---------------------------
passwordKey = '-PASSSWORD-'
passwordPrompt = 'Enter your password'
currentPassword = ''

# Seriously though this is some test data getting pushed to a public repository...
salt = 'SomeVeryFakeSaltThatIsOnlyUsedForTesting5618644984981353486'
hash = b'o`\x07\xe3\x96\xd5\xa7\xf2\xf1\xa0\x1c|>q\xdec7\xe7\xfc\xf1L\x81u\xcf\xfbp\xbc%\xe0\x1f\xce\xe1\xd4\x96\x91\xce\x0c>\xc8\x91p>G7\xbc\xc9;\xf5i\xd7\xf6dS\xbdd\xa8\xa7/:1\xd8\xfb|\xcf'

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

def authenticate(tepidPassword):
    ok = (hash == scrypt.hash(tepidPassword, salt))
    log(f'Authentication of "{tepidPassword}" was {ok}');
    return ok

def authenticated():
    '''Actions taken when user is successfully verified'''
    log('Access Granted!')

def clear_password():
    '''Clear the current password being stored and the display'''
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
            clear_password()

        elif event == 'Submit':
            authenticate(currentPassword)
            clear_password()

        if event in (sg.WIN_CLOSED, 'Quit'):
            sg.popup("Closing")
            break

except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")