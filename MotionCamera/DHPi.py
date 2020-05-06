from __future__ import print_function
from datetime import datetime
from lifxlan import LifxLAN
from enum import Enum

import sys
import argparse
import time
import numpy as np
import cv2
import imutils

# Get arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size before motion detection")
argParser.add_argument("-r", "--refresh-time", type=int, default=60, help="Amount of seconds before static image refresh")
argParser.add_argument("-m", "--motion-time", type=int, default=300, help="Amount of seconds after last motion event to still be considered active")
argParser.add_argument("-t", "--threshold", type=int, default=30, help="Amount of difference between images")
argParser.add_argument('--ononly', dest='ononly', action='store_true', help="Disable turning lights off command")
argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
argParser.set_defaults(interactive=True)
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
min_area = args["min_area"]
refresh_time = args["refresh_time"]
img_threshold = args["threshold"]
interactive = args["interactive"]
motion_time = args["motion_time"]
quiet = args["quiet"]
ononly = args["ononly"]
print(f"Args: {args}")

# ------------------------- DEFINE GLOBALS -------------------------
firstFrame = None
staticImgLastRefresh = datetime.now()
lastMotionDetectionEvent = datetime.now()
lastLightOffEvent = None
officeLightGroup = None
officeLights = None
lifx = None
ProgramState = Enum("ProgramState", "on off stale")
lastState = ProgramState.off
imgCount = 1

# ------------------------- DEFINE FUNCTIONS -------------------------
# Process the initial image frame from the camera
def processFrame(frame):
    frame = imutils.resize(frame, width=500)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.GaussianBlur(frame, ksize=(21, 21), sigmaX=0)
    return frame

# Print message to console with timestamp
def timestampDebug(text, displayWhenQuiet = False):
    if displayWhenQuiet or not quiet:
        curr_time = datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
        print (curr_time + ": " + text)

def shouldUpdateStaticImage(now):
    if firstFrame is None:
        timestampDebug("Background reset")
        return True
    
    lastUpdateDelta = now - staticImgLastRefresh
    if lastUpdateDelta.seconds >= refresh_time:
        timestampDebug("Background refresh limit reached")
        return True

    return False

def saveMotionImage(frame):
    global imgCount
    curr_time = datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
    filePath = '/home/pi/Desktop/DHPi/MotionImages/' + curr_time + '-' + str(imgCount) + '.png'
    cv2.imwrite(filePath, frame)
    imgCount+=1

def lightOnSequence():
    officeOne.set_power("on", duration=5000)
    sleep(1)
    officeTwo.set_power("on", duration=4000)
    sleep(1)
    officeThree.set_power("on", duration=3000)

# ------------------------- DEFINE INITIALIZE -------------------------
# Init camera with camera warmup
timestampDebug("Initializing...")
camera = cv2.VideoCapture(0)

lifx = LifxLAN(7)
officeLightGroup = lifx.get_devices_by_group("Office")
officeLights = officeLightGroup.get_device_list()

if len(officeLights) < 3:
    timestampDebug(f"Did not discover all office lights! ({len(officeLights)} of 3)")
    sys.exit(-1)

officeOne = next(filter(lambda l: l.get_label() == "Office One", officeLights), None)
officeTwo = next(filter(lambda l: l.get_label() == "Office Two", officeLights), None)
officeThree = next(filter(lambda l: l.get_label() == "Office Three", officeLights), None)
officeLightGroup.set_power("on", rapid=True)

timestampDebug("Initialized.")
timestampDebug("Running...")

# ------------------------- DEFINE RUN -------------------------
while True:
    loopStart = datetime.now()
    (okFrame, frame) = camera.read()
    frame = imutils.resize(frame, width=480, height=480)
    frame = imutils.rotate(frame, angle=270)
    p_frame = processFrame(frame)


    # Deal with background updates
    if lastLightOffEvent is not None:
        lightOffDelta = loopStart - lastLightOffEvent
        if lightOffDelta.seconds <= 15:
            timestampDebug(f"Clearing buffer after power off - {15 - lightOffDelta.seconds} seconds remaining.")
            continue
        else:
            timestampDebug("Listening to changes again", displayWhenQuiet=True)
            lastLightOffEvent = None
            firstFrame = None

    if shouldUpdateStaticImage(loopStart):
        staticImgLastRefresh = loopStart
        firstFrame = p_frame
        continue

    frameDelta = cv2.absdiff(firstFrame, p_frame)
    threshold = cv2.threshold(frameDelta, img_threshold, 255, cv2.THRESH_BINARY)[1]

    # Dilate movement areas
    threshold = cv2.dilate(threshold, None, iterations=2)
    contours = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    # Check to see if motion has occurred
    loopMotion = False
    for c in contours:
        # Motion detected but not triggered
        motionSize = cv2.contourArea(c)
        if motionSize < min_area:
            #timestamp('Ignored motion with size (' + str(motionSize) + ')')
            continue
        else:
            # motion dectected.
            loopMotion = True
            lastMotionDetectionEvent = loopStart
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color=(0, 255, 0), thickness=2)

    # Update feed!
    motionStatus = "Unoccupied"
    lastMotionDelta = loopStart - lastMotionDetectionEvent
    if loopMotion and lastState == ProgramState.off:
        timestampDebug("Motion detected! Powering lights on...", displayWhenQuiet=True)
        lightOnSequence()

        lastState = ProgramState.on
        motionStatus =  "Occupied"
        lastLightOffEvent = None
        saveMotionImage(frame)
    elif lastMotionDelta.seconds <= motion_time:
        # do nothing, motion is stale
        timestampDebug(f"Motion stale for {lastMotionDelta.seconds}secounds")

        lastState = ProgramState.stale
        motionStatus =  f"Occupied (Stale: {lastMotionDelta.seconds}seconds)"
        lastLightOffEvent = None
    elif lastMotionDelta.seconds > motion_time and lastState != ProgramState.off:
        timestampDebug(f"No motion detected.", displayWhenQuiet=True)
        firstFrame = None
        lastState = ProgramState.off
        motionStatus =  "Unoccupied"
        
        # wait for lights to full turn off then update
        if not ononly:
            officeLightGroup.set_power("off", rapid=True)
            lastLightOffEvent = loopStart

    cv2.putText(frame, "Status: {}".format(motionStatus), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    if (interactive):
        cv2.imshow('Feed', frame)
        if firstFrame is not None: cv2.imshow('Static', firstFrame)
        cv2.imshow('Threshold', threshold)
        #cv2.imshow('Delta', frameDelta)

    keyPressed = cv2.waitKey(1) & 0xFF
    if keyPressed == ord('q'): 
        break
    elif keyPressed == ord('r'):
        firstFrame = None

camera.release()
cv2.destroyAllWindows()