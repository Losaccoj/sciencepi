# detect motion in a video feed.
import os
import datetime
import time
from collections import deque
from itertools import islice
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import RPi.GPIO as GPIO

# setup GPIO triggers
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# init camera, defaults, and grab a reference.
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(640, 480))
fourcc = cv2.VideoWriter_fourcc(*"MJPG")

# interrupts
GPIO.add_event_detect(21,GPIO.FALLING)
GPIO.add_event_detect(23,GPIO.FALLING)

# warmup
time.sleep(0.2)

# hold one minute in memory.
old_frames = deque() #TODO! deque(maxlen=int(30*1*60)))
triggered = None # prevent multiple triggers
timestamp = None
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    if GPIO.event_detected(21) and triggered == None:
        cv2.putText(image, str('TRIGGER'), (10,image.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255),1)
        triggered = 1
        timestamp = len(old_frames)
        # maybe use limited deque until this trigger then switch??
        print('TRIGGERED!')
    image = frame.array
    old_frames.append(image)
    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF
    rawCapture.truncate(0)
    if key == ord("q") or GPIO.event_detected(23):
        break



# post hoc timestamping
exp_timer=0
print('timestamping experiment')
if timestamp is not None:
    for f in islice(old_frames,timestamp, len(old_frames)):
        cv2.putText(f, str(exp_timer), (10,f.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255),1)
        exp_timer+=0.033

# name file
timenow = datetime.datetime.now()
filename =os.path.join(os.getcwd(), timenow.strftime("%Y-%m-%d_%H%M") + ".avi")
pic_name = os.path.join(os.getcwd(), timenow.strftime("%Y-%m-%d_%H%M") + "_triggerpic.jpg")


# write picture at trigger
cv2.imwrite(pic_name, old_frames[timestamp-1])


# opencv writer
writer = cv2.VideoWriter(filename, fourcc, 30,(640,480), True)

# write and save it
print('writing {} with opencv'.format(filename))
for b in old_frames:
    writer.write(b)
print('done')
