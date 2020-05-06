from collections import deque
import numpy as np
import cv2
import imutils
import argparse

kernel = np.ones((5,5),np.uint8)
pts = deque(maxlen=64)

#parser = argparse.ArgumentParser(description = 'Record training images for Pi Wand Tracker')
#parser.add_argument('path', type='string', help='File path to save images to')
#parser.add_argument()

# initialize camera and size window size as 640px by 480px
camera = cv2.VideoCapture(0)

imgCount = 1
thresh = 40
# loop over the set of tracked points so that we can draw a line for human eyes.
def drawTrackingLine():
    for i in range(1, len(pts)):
        # if either of the tracked points are None, ignore them
        if pts[i - 1] is None or pts[i] is None:
            continue

        # otherwise, draw the connecting lines
        cv2.line(frame_gray, pts[i - 1], pts[i], (255, 0, 0), thickness = 5)

while 1:
    # read from camera
    (grabbed, frame) = camera.read()
    frame = imutils.rotate(frame, angle=180)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # TODO determine if this completely necessary
    cv2.equalizeHist(frame_gray)

    # resize image for faster processing.
    #frame_gray = cv2.resize(frame_gray, (120, 120), interpolation = cv2.INTER_CUBIC)

    # find the point by looking for pixels >threshold
    th, frame_gray = cv2.threshold(frame_gray, thresh, 255, cv2.THRESH_BINARY)

    # At least 1 pass is needed to create centroid for recognition
    # This approach may not be needed if Hough circles are used.
    frame_gray = cv2.dilate(frame_gray, kernel, iterations = 1)
 
    # find contours in the mask
    # countours meaning the binary area (aka in our case, the white dot).
    cnts = cv2.findContours(frame_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None
 
	# only proceed if at least one contour was found
    if len(cnts) > 0:
        # TODO maybe should change this to assume the cnt that is closest to center of frame is the most applicable instead of max.
		# find the most applicable contour in the mask (in this case the largest), then use it to compute the minimum enclosing circle and if it matches a known spell.
        mostLikelyWandTip = max(cnts, key=cv2.contourArea)

        # find bounds of circle in order to show on screen. Not applicable in this sense
        # ((x, y), radius) = cv2.minEnclosingCircle(c)

        # Moments help find centers of points
        # https://www.learnopencv.com/find-center-of-blob-centroid-using-opencv-cpp-python/
        M = cv2.moments(mostLikelyWandTip)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

	# update the points queue
    pts.appendleft(center)

    # TODO control view port/this extra work by argument
    drawTrackingLine()

    # detect likely spell if the number of tracked points is >=50%
    numPointsTracked = sum(1 for p in pts if p is not None)
    if numPointsTracked == len(pts):
        filePath = '/home/pi/Desktop/WandTraining/Shapes/HorizontalLine/' + 'shape2-' + str(imgCount) + '.png'
        print(filePath)
        cv2.imwrite(filePath, frame_gray)
        imgCount+=1

    # loop and show frame
    cv2.imshow('raw', frame)
    cv2.imshow('raw-grey', frame_gray)
    keyPressed = cv2.waitKey(1) & 0xFF
    if keyPressed == ord('q'):
        break
    elif keyPressed == ord('p'):
        cv2.imwrite('home/pi/picameraalanTest.png', frame_gray)
        imgCount+=1
    # increase threshold if 't' is pressed, decrease for 'g'
    elif keyPressed == ord('t'):
        thresh = thresh + 10
        print('Threshold:' + str(thresh))
    elif keyPressed == ord('g'):
        thresh = thresh - 10
        print('Threshold:' + str(thresh))

    
# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
