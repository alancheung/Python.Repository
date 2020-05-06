from collections import deque
import numpy as np
import cv2
import imutils
import time

argParser = argparse.ArgumentParser()
argParser.add_argument("-b", "--buffer", type=int, default=64, help="Amount of points to be tracked")
argParser.add_argument("-m", "--motion-buffer", type=int, default=32, help="Amount of tracked points to consider motion")
argParser.add_argument("-t", "--threshold", type=int, default=40, help="Threshold for detection point of light")
argParser.add_argument('--remote', dest='interactive', action='store_false', help="Disable Pi hardware specific functions")
argParser.set_defaults(interactive=True)
argParser.add_argument('--quiet', dest='quiet', action='store_true', help="Disable logging")
argParser.set_defaults(quiet=False)

args = vars(argParser.parse_args())
buffer = args["buffer"]
motion_buffer = args["motion_buffer"]
threshold = args["threshold"]
interactive = args["interactive"]
motion_time = args["motion_time"]
quiet = args["quiet"]
print(f"Args: {args}")

pts = deque(maxlen=buffer)
kernel = np.ones((5,5),np.uint8)
lastCompleteMotion = None

# Initialize camera with 2s delay for camera to warm up
camera = cv2.VideoCapture(0)
time.sleep(2)

while True:
    # read from camera
    (grabbed, frame) = camera.read()
    frame = imutils.rotate(frame, angle=180)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.equalizeHist(frame_gray)

    # find the point by looking for pixels >threshold
    th, frame_gray = cv2.threshold(frame_gray, threshold, 255, cv2.THRESH_BINARY)

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

        # Moments help find centers of points
        # https://www.learnopencv.com/find-center-of-blob-centroid-using-opencv-cpp-python/
        M = cv2.moments(mostLikelyWandTip)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

	# update the points queue
    pts.appendleft(center)

    # what is the current number of tracked points?!
    numPointsTracked = sum(1 for p in pts if p is not None)
    if numPointsTracked >= motion_buffer:
        print(f"Motion tracked with {numPointsTracker} of {motion_buffer} points.")
        

    # loop and show frame
    if interactive:
        cv2.imshow('raw', frame)
        cv2.imshow('raw-grey', frame_gray)
        keyPressed = cv2.waitKey(1) & 0xFF
        if keyPressed == ord('q'):
            break
        # increase threshold if 't' is pressed, decrease for 'g'
        elif keyPressed == ord('t'):
            threshold = threshold + 10
            print('Threshold:' + str(threshold))
        elif keyPressed == ord('g'):
            threshold = threshold - 10
            print('Threshold:' + str(threshold))

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
