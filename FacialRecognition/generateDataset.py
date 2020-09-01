''''
Capture multiple Faces from multiple users to be stored on a DataBase (dataset directory)
	==> Faces will be stored on a directory: dataset/ (if does not exist, pls create one)
	==> Each face will have a unique numeric integer ID as 1, 2, 3, etc                       
Based on original code by:
Anirban Kar: https://github.com/thecodacus/Face-Recognition 
Marcelo Rovai - MJRoBot.org @ 21Feb18: https://github.com/Mjrovai/OpenCV-Face-Recognition/blob/master/FacialRecognition/01_face_dataset.py
'''

import cv2
import os

cam = cv2.VideoCapture(0)
#cam.set(3, 640) # set video width
#cam.set(4, 480) # set video height

face_detector = cv2.CascadeClassifier('/home/pi/Project/FacialRecognition/haar_frontface_default.xml')

# For each person, enter one numeric face id
face_id = input('\n enter user id end press <return> ==>  ')

print("\n [INFO] Initializing face capture. Look the camera and wait ...")
# Initialize individual sampling face count
count = 0

while(True):
    ret, img = cam.read()
    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE) 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #faces = face_detector.detectMultiScale(gray, 1.3, 5)
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(20, 20))

    for (x,y,w,h) in faces:

        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
        count += 1

        # Save the captured image into the datasets folder
        cv2.imwrite("/home/pi/Project/FacialRecognition/dataset/user." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])
        cv2.imshow(f'image: {count}', img)

    k = cv2.waitKey(100) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break
    elif count >= 30: # Take 30 face sample and stop video
         break

# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()