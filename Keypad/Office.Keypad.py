'''
This module uses OpenCV and plain Python libraries to mimic a smart lock entry.
Offers users 3 ways of authenticating and triggering the relay.
1) Keypad entry
2) RFID
3) Facial recognition
'''
# ------------------------- DEFINE IMPORTS ---------------------------
# System imports
from __future__ import print_function
from datetime import datetime, time, timedelta
import argparse
import time
import json
import requests

# UI
import PySimpleGUI as sg

# Hashing
import scrypt
import os

# PiCamera imports
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import base64

# GPIO
from mfrc522 import SimpleMFRC522
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")


# ------------------------- DEFINE ARGUMENTS -------------------------
# argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
#argParser.add_argument("--ononly", dest="ononly", action="store_true", help="Disable turning lights off command")
#argParser.add_argument("--remote", dest="interactive", action="store_false", help="Disable Pi hardware specific functions")
#argParser.set_defaults(interactive=True)

argParser = argparse.ArgumentParser()
argParser.add_argument("--quiet", dest="quiet", action="store_true", help="Disable informational logging")
argParser.add_argument("-f", "--log-file", default=None, help="Specify file to log to.")
argParser.add_argument("-p", "--relay-pin", type=int, default=4, help="GPIO number that relay is connected to.")
argParser.add_argument("-o", "--open-time", type=int, default=3, help="Number of seconds to keep relay open (and lock unlocked).")
argParser.add_argument("-s", "--server", default="http://dhcpi:3000", help="Server address to send log messages to")
argParser.add_argument("-b", "--base-directory", default=".", help="Directory that project files are stored in. Default to currently active directory.")

argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
quiet = args["quiet"]
logFileName = args["log_file"]
relayPin = args["relay_pin"]
openTime = args["open_time"]
server = args["server"]
baseDirectory = args["base_directory"]

# ------------------------- DEFINE GLOBALS ---------------------------
passwordKey = "-PASSSWORD-"
captureKey = "-CAMERACAPTURE-"

passwordPrompt = "Enter your password"
currentPassword = ""

# Layout sizes, assuming touchscreen of 800, 480 pixels
numButtonSize = (12, 4)
fullWidth = 45
captureImageSize = (400, 480)

lastRfidTime = datetime.now()

# File paths and directory locations
authFilePath = f"{baseDirectory}/authentication.json"
faceCascadeXMLPath = f"{baseDirectory}/haar_frontface_default.xml"
guestListPath = f"{baseDirectory}/guest_list.yml"
if logFileName is not None:
    logFileName = f"{baseDirectory}/{logFileName}"

# ------------------------- DEFINE FUNCTIONS -------------------------
def log(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        now = datetime.now().strftime("%H:%M:%S")
        message = f"{now}: {text}"
        if logFileName is not None:
            with open(logFileName, "a") as fout:
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
        window[passwordKey].update("*" * len(currentPassword))
    window.Finalize()

def update_password_prompt(message):
    window[passwordKey].update(message)
    window.Finalize()

def authenticate(tepidPassword, type):
    tepidPassword = str(tepidPassword)
    hex = str(scrypt.hash(tepidPassword, salt).hex())

    try:
        log(f"Sending authentication to {server}")
        authRequest = {
	        "ID": "",
	        "Hash": hex,
	        "Type": type,
	        "ClientId": clientId,
	        "ClientKey": clientKey
        }

        req = requests.post(f"{server}/authorization/authenticate", data = authRequest)
        if (req.status_code == 200):
            alrt("Authenticated user!")
            return True
        elif (req.status_code == 401):
            err("Wrong password!")
            update_password_prompt("ACCESS DENIED")
            return False
        else:
            err(f"Request status code did not indicate success ({req.status_code})!");
            update_password_prompt("ACCESS DENIED: Server Error")
            return False
    except Exception as ex:
        err(f"Could not authenticate due to {type(ex).__name__}!")
        update_password_prompt("ACCESS DENIED: Error")
        return False
    
    update_password_prompt("ACCESS DENIED")
    err("Fell through authentication!")
    return False

def authenticate_facial(faces):
    # Eh okay with more than one faces, just see if any match a trusted user.
    if (faces is None or len(faces) <= 0):
        err("No faces found!")
        update_password_prompt("ACCESS DENIED: No faces detected")
        return False, None
        
    # Okay lets check the faces now I guess
    for face in faces:
        grayFace = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        id, confidenceIndex = doorman.predict(grayFace)

        # confidenceIndex will be 0 if perfect match
        name = allowedFaces[id]
        confidence = round(100 - confidenceIndex)
        alrt(f"Identified: {name} with confidence {confidence}%.")

        # This should probably be higher
        if (confidence > 40):
            return (authenticate(name, "FACE"), name)
        else:
            update_password_prompt("ACCESS DENIED: You seem familiar..")
            return False, None
        
    update_password_prompt("ACCESS DENIED")
    err("Fell through authentication (facial)!")
    return False, None

def clear():
    '''Clear the current password being stored and the displays'''
    global currentPassword
    currentPassword = ""
    update_password_count()

    window[captureKey].update(data=None)
    window.Finalize()

def open_sesame():
    # Connect NC relay connections and open door.
    GPIO.output(relayPin, GPIO.HIGH)
    time.sleep(openTime)
    GPIO.output(relayPin, GPIO.LOW)

    clear()

def take_picture():
    update_password_prompt("Smile! Working...")

    # Fire up camera to take picture, but leave camera off normally.
    with PiCamera() as camera:
        camera.rotation = 90
        rawCapture = PiRGBArray(camera)
        time.sleep(1) # Camera warm-up time

        camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        rawCapture.truncate(0)
    log("Image taken!")

    return image

def detect_faces(image):
    '''
    Given an image:
    1) Convert the image to gray-scale
    2) Detect the number of faces in the image
        ---2a) Draw a square around all of the faces
        2b) Cut out the face from the image
    3) Return all found faces as images
    '''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detected = faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(20, 20))
    faces = []

    log(f"Found {len(detected)} faces!")
    for (x, y, w, h) in detected:
        # Steal the face before drawing the square!
        faces.append(image[y:y+h, x:x+w])
        #cv2.rectangle(image, (x,y), (x+w,y+h), (255,0,0), 2)

    return faces

def convert_to_binary_encoded_base64(image):
    '''Resize to "captureImageSize" and converts the given image to a base64 encoded string image.'''
    resizedImage = cv2.resize(image, captureImageSize)
    retval, buffer = cv2.imencode(".png", resizedImage)
    png_as_text = base64.b64encode(buffer)
    return png_as_text

# ------------------------- DEFINE INITIALIZE ------------------------
log("Initializing...", displayWhenQuiet = True)
log(f"Args: {args}", displayWhenQuiet = True)

try:
    with open(authFilePath) as authFile:
        authInfo = json.load(authFile)
        log("File loaded!")
except FileNotFoundError:
    err(f"'{authFilePath}' could not be found!")
    sys.exit(-1)

salt = authInfo["salt"]
allowedFaces = ["None"] + authInfo["allowedFaces"]
clientId = authInfo["myId"]
clientKey = authInfo["myKey"]
log("Default authentication loaded!")

pictureLayout = [[sg.Image(r"", size=captureImageSize, key=captureKey)]]
keypadLayout = [[sg.Text(passwordPrompt, key=passwordKey, size=(fullWidth, 2), font="Any 18")],
                [sg.Button("7", size=numButtonSize), sg.Button("8", size=numButtonSize), sg.Button("9", size=numButtonSize)],
                [sg.Button("4", size=numButtonSize), sg.Button("5", size=numButtonSize), sg.Button("6", size=numButtonSize)],
                [sg.Button("1", size=numButtonSize), sg.Button("2", size=numButtonSize), sg.Button("3", size=numButtonSize)],
                [sg.Button("Clear", size=numButtonSize), sg.Button("0", size=numButtonSize), sg.Submit("Submit", size=numButtonSize)],
                [sg.Button("Face Recognition", size=(fullWidth, 4))]]
layout = [[sg.Column(pictureLayout), sg.Column(keypadLayout)]]
log("GUI layout set!")

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers
GPIO.setup(relayPin, GPIO.OUT) # GPIO Assign mode
log("GPIO relay initialized!")

rfidReader = SimpleMFRC522()
log("RFID reader initialized!")

faceCascade = cv2.CascadeClassifier(faceCascadeXMLPath)
doorman = cv2.face.LBPHFaceRecognizer_create()
doorman.read(guestListPath)
log("CV2 face initialized!")

# ------------------------- DEFINE RUN -------------------------------
log("Initialized!", displayWhenQuiet = True)
log("Running...", displayWhenQuiet = True)
try:
    showKeypad = True
    #, no_titlebar=True, location=(0,0), size=piTouchSize, keep_on_top=True
    window = sg.Window("Keypad", layout, no_titlebar=True, location=(0,0), size=(800, 480), keep_on_top=False)
    window.Finalize()

    while showKeypad:
        # Stop spamming RFID reader
        now = datetime.now()
        timeSinceRfid = now - lastRfidTime
        if timeSinceRfid.seconds > 1:
            rfidId, rfidData = rfidReader.read_no_block()
        else:
            rfidId = None
            rfidData = None

        # Regularly read from the window
        event, values = window.read(1)
        
        if rfidId is not None:
            lastRfidTime = datetime.now()
            if authenticate(rfidId, "RFID"):
                update_password_prompt("ACCESS GRANTED")
                open_sesame()
            else:
                window[passwordKey].update("ACCESS DENIED")
                window.Finalize()
        elif event is not sg.TIMEOUT_EVENT:
            # If numerical input assume user has hit an actual key.
            if (str(event).isnumeric()):
                currentPassword += str(event)
                update_password_count()
        
            # Clear event delegates to method.
            elif event == "Clear":
                clear()

            # Confirm if authenticated user by password
            elif event == "Submit":
                submission = currentPassword
                clear()

                # authenticate sets denied messages
                if authenticate(submission, "KEYPAD"):
                    update_password_prompt("ACCESS GRANTED")
                    open_sesame()

            # Confirm authenticated user by facial recognition
            elif event == "Face Recognition":
                clear()

                # Take and find all faces in the image.
                image = take_picture()
                faces = detect_faces(image)

                # Display either a face if one was found or the camera picture
                if (len(faces) > 0):
                    b64Image = convert_to_binary_encoded_base64(faces[0])
                else:
                    b64Image = convert_to_binary_encoded_base64(image)
                window[captureKey].update(data=b64Image)
                window.Finalize()

                # authenticate_facial sets denied status messages
                authenticated, name = authenticate_facial(faces)
                if authenticated:
                    update_password_prompt(f"Welcome, {name}!")
                    open_sesame()

            # This captures the Ctrl-C and exit button events
            elif event in (sg.WIN_CLOSED, "Quit"):
                #sg.popup("Closing")
                break
        else:
            # Nothing to see here.
            continue

except KeyboardInterrupt:
    log("KeyboardInterrupt caught! Cleaning up...")
finally:
    GPIO.cleanup()
    log("Program exiting...")