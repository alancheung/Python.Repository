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
import json
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
passwordKey = '-PASSSWORD-'
captureKey = '-CAMERACAPTURE-'

passwordPrompt = 'Enter your password'
currentPassword = ''

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
    ok = (hashHex == scrypt.hash(tepidPassword, salt).hex())
    log(f'Authentication was {ok}');
    return ok

def authenticate_facial(image):
    log("TODO")

def open_sesame():
    window[passwordKey].update('ACCESS GRANTED').Finalize()
    
    # Connect NC relay connections and open door.
    GPIO.output(relayPin, GPIO.HIGH)
    time.sleep(openTime)
    GPIO.output(relayPin, GPIO.LOW)
def clear():
    '''Clear the current password being stored and the displays'''
    global currentPassword
    currentPassword = ''
    update_password_count()

    window[captureKey].update(data=None)

def take_picture():
    # Fire up camera to take picture, but leave camera off normally.
    with PiCamera() as camera:
        camera.rotation = 90
        rawCapture = PiRGBArray(camera)
        time.sleep(1) # Camera warm-up time

        camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        rawCapture.truncate(0)
    log('Image taken!')
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

try:
    with open("/home/pi/Project/authentication.json") as saltHashFile:
        saltHash = json.load(saltHashFile)
        log("File loaded!")
except FileNotFoundError:
    err("'/home/pi/Project/authentication.json' could not be found!")
    sys.exit(-1)

salt = saltHash["salt"]
hashHex = saltHash["hashHex"]
log("Default authentication loaded!")

pictureLayout = [[sg.Image(r'', size=captureImageSize, key=captureKey)]]
keypadLayout = [[sg.Text(passwordPrompt, key=passwordKey, size=(fullWidth, 2), font='Any 18')],
                [sg.Button('7', size=numButtonSize), sg.Button('8', size=numButtonSize), sg.Button('9', size=numButtonSize)],
                [sg.Button('4', size=numButtonSize), sg.Button('5', size=numButtonSize), sg.Button('6', size=numButtonSize)],
                [sg.Button('1', size=numButtonSize), sg.Button('2', size=numButtonSize), sg.Button('3', size=numButtonSize)],
                [sg.Button('Clear', size=numButtonSize), sg.Button('0', size=numButtonSize), sg.Submit('Submit', size=numButtonSize)],
                [sg.Button('Face Recognition', size=(fullWidth, 4))]]
layout = [[sg.Column(pictureLayout), sg.Column(keypadLayout)]]
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
    window = sg.Window('Keypad', layout, no_titlebar=True, location=(0,0), size=(800, 480), keep_on_top=False).Finalize()

    while showKeypad:
        event, values = window.read()
        log(event)

        # If numerical input assume user has hit an actual key.
        if (str(event).isnumeric()):
            currentPassword += str(event)
            update_password_count()
        
        # Clear event delegates to method.
        elif event == 'Clear':
            clear()

        # Confirm if authenticated user by password
        elif event == 'Submit':
            submission = currentPassword
            clear()

            if authenticate(submission):
                open_sesame()
            else:
                window[passwordKey].update('ACCESS DENIED')

        # Confirm authenticated user by facial recognition
        elif event == 'Face Recognition':
            clear()

            # Use fullsized 'image' object for facial recog
            image = take_picture()

            b64Image = convert_to_binary_encoded_base64(image)
            window[captureKey].update(data=b64Image)

        # This captures the Ctrl-C and exit button events
        elif event in (sg.WIN_CLOSED, 'Quit'):
            #sg.popup("Closing")
            break

except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")
finally:
    GPIO.cleanup()
    log("Program exiting...")