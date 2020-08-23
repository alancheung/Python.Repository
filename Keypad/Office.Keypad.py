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
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import base64

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
captureKey = '-CAMERACAPTURE-'

passwordPrompt = 'Enter your password'
currentPassword = ''

# Seriously though this is some test data getting pushed to a public repository...
salt = 'SomeVeryFakeSaltThatIsOnlyUsedForTesting5618644984981353486'
hash = b'o`\x07\xe3\x96\xd5\xa7\xf2\xf1\xa0\x1c|>q\xdec7\xe7\xfc\xf1L\x81u\xcf\xfbp\xbc%\xe0\x1f\xce\xe1\xd4\x96\x91\xce\x0c>\xc8\x91p>G7\xbc\xc9;\xf5i\xd7\xf6dS\xbdd\xa8\xa7/:1\xd8\xfb|\xcf'

# Layout sizes, assuming touchscreen of 800, 480 pixels
numButtonSize = (12, 4)
fullWidth = 45
captureImageSize = (400, 480)

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
    if len(currentPassword) == 0:
        window[passwordKey].update(passwordPrompt)
    else:
        window[passwordKey].update('*' * len(currentPassword))

def authenticate(tepidPassword):
    ok = (hash == scrypt.hash(tepidPassword, salt))
    log(f'Authentication of "{tepidPassword}" was {ok}');
    return ok

def open_sesame():
    print("Opening relay!")

def clear():
    '''Clear the current password being stored and the displays'''
    global currentPassword
    currentPassword = ''
    update_password_count()

    window[captureKey].update(data=None)

def take_picture():
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    rawCapture.truncate(0)
    log('Image taken!')

    #cv2.imshow('Capture', image)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return image

def convert_to_binary_encoded_base64(image):
    '''Resize to 'captureImageSize' and converts the given image to a base64 encoded string image.'''
    resizedImage = cv2.resize(image, captureImageSize)
    retval, buffer = cv2.imencode('.png', resizedImage)
    png_as_text = base64.b64encode(buffer)
    return png_as_text

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

pictureLayout = [[sg.Image(r'', size=captureImageSize, key=captureKey)]]
keypadLayout = [[sg.Text(passwordPrompt, key=passwordKey, size=(fullWidth, 2), font='Any 18')],
                [sg.Button('7', size=numButtonSize), sg.Button('8', size=numButtonSize), sg.Button('9', size=numButtonSize)],
                [sg.Button('4', size=numButtonSize), sg.Button('5', size=numButtonSize), sg.Button('6', size=numButtonSize)],
                [sg.Button('1', size=numButtonSize), sg.Button('2', size=numButtonSize), sg.Button('3', size=numButtonSize)],
                [sg.Button('Clear', size=numButtonSize), sg.Button('0', size=numButtonSize), sg.Submit('Submit', size=numButtonSize)],
                [sg.Button('Face Recognition', size=(fullWidth, 4))]]
layout = [[sg.Column(pictureLayout), sg.Column(keypadLayout)]]

camera = PiCamera()
camera.rotation = 90
rawCapture = PiRGBArray(camera)
time.sleep(2)

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    showKeypad = True
    #, no_titlebar=True, location=(0,0), size=piTouchSize, keep_on_top=True
    window = sg.Window('Keypad', layout, no_titlebar=True, location=(0,0), size=(800, 480), keep_on_top=False).Finalize()

    while showKeypad:
        event, values = window.read()
        print(event)

        # If numerical input assume user has hit an actual key.
        if (str(event).isnumeric()):
            currentPassword += str(event)
            update_password_count()

        elif event == 'Clear':
            clear()

        elif event == 'Submit':
            submission = currentPassword
            clear()

            if authenticate(submission):
                window[passwordKey].update('ACCESS GRANTED')
                open_sesame()
            else:
                window[passwordKey].update('ACCESS DENIED')

        elif event == 'Face Recognition':
            clear()

            # Use fullsized 'image' object for facial recog
            image = take_picture()

            b64Image = convert_to_binary_encoded_base64(image)
            window[captureKey].update(data=b64Image)



        if event in (sg.WIN_CLOSED, 'Quit'):
            #sg.popup("Closing")
            break

except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")