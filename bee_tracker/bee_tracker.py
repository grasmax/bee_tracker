from __future__ import print_function
from __future__ import division

import numpy as np
import cv2
import sys
import argparse

from time import sleep
from video_source import VideoSource
from web_stream import WebcamServerThread
from image_processor import frameData
from image_processor import ImageProcessor
from database_connector import DatabaseConnectionThread

def main():

    # Parse and check command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--system", type=str, default="Windows", help="System: Use Windows or Raspi (default = Windows)")
    ap.add_argument("-v", "--videosource", type=str, default="0", help="Video source: Use 0 for camera or path to video (default = 0)")
    ap.add_argument("-f", "--fps", type=int, default=30, help="Frame rate in fps (default = 30)")
    ap.add_argument("-b", "--begin", type=int, default=0, help="Start of video in ms (default 0)")
    ap.add_argument("-l", "--length", type=int, default=-1, help="Length of video in ms (-1 = infinite, default = -1)")
    ap.add_argument("-rx", "--resolutionx", type=int, default=640, help="Resolution of video: x (default = 640)")
    ap.add_argument("-ry", "--resolutiony", type=int, default=480, help="Resolution of video: y (default = 480)")
    ap.add_argument("-roix", "--regionofintx", type=int, default=0, help="Region of interest: x (default = 0)")
    ap.add_argument("-roiy", "--regionofinty", type=int, default=0, help="Region of interest: y (default = 0)")
    ap.add_argument("-roiw", "--regionofintw", type=int, default=640, help="Region of interest: width (default = 640)")
    ap.add_argument("-roih", "--regionofinth", type=int, default=480, help="Region of interest: height (default = 480)")
    args = vars(ap.parse_args())

    # Create the camera / video source handler
    videoSource = VideoSource.createVideoStream(args["system"], args["videosource"], args["fps"], args["resolutionx"], args["resolutiony"], args["begin"])

    # Wait 1s (important when camera is in use in order to have it properly started)
    sleep(1)

    # Initialize frame data object (used to share video data between threads)
    listFrameData = [ frameData(args) for i in range(2)]
 

    # Start the thread which handles the webcam stream
    wst = WebcamServerThread(args, listFrameData)
    wst.start()

    # Initialize the value list object (used to share measurement values between threads)
    valueList = {
        'date': '2017-01-01',
        'time': '00:00:00',
        'bees': 0,
        'light': 0
        }

    # Start the thread which handles the database connection
    #dbt = DatabaseConnectionThread(args["system"], "bee_activity", "beeactivity_2", valueList, 30) 
    #dbt.start()

    # Start the image processing
    ImageProcessor.processVideoStream(listFrameData, valueList, videoSource)


####
####



if __name__ == "__main__":
    main()