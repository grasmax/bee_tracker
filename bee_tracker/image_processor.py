from __future__ import print_function
from __future__ import division

import numpy as np
import cv2
import threading

from time import sleep

class EnumStatus():
    empty            = "empty"
    calc_beg         = "calc_beg"
    calc_end         = "calc_end"
    addframes_beg    = "addframes_beg"
    addframes_end    = "addframes_end"
    web_beg          = "web_beg"
    web_end          = "web_end"
    
class roiRectangle():

    x1 = 0
    x2 = 0
    y1 = 0
    y2 = 0
    w = 0
    h = 0

    def __init__(self, args):

        self.x1 = args["regionofintx"]
        self.y1 = args["regionofinty"]
            
        self.w = args["regionofintw"]
        self.h = args["regionofinth"]

        self.x2 = self.x1 + self.w
        self.y2 = self.y1 + self.h

class frameData():

    # General data
    system = "Windows"

    # Video configuration data
    roiRect = None
    fps = 30

    # Video data
    rawFrame = None
    roiFrame = None
    roiFrameGray = None
    roiFrameSubtract = None
    contours = None
    moments = None
    centers = None

    #wird zur static-Member!! status = 0
 
    terminateWebThread = 0   
    evWebThreadTerminate = threading.Event()

    countCalc = 0
    countDraw = 0
    countWeb = 0

    def __init__(self, args, nr):
        self.nr = nr + 1   
        self.roiRect = roiRectangle(args)
        self.fps = args["fps"]
        self.system = args["system"]
        self.x_lock = threading.Lock()
        self.img = None
        self.status = EnumStatus.empty

    def SetStatus( self, newStatus):
        self.x_lock.acquire()

        ret = 0
        if newStatus == EnumStatus.calc_beg:
            if self.status == EnumStatus.empty or self.status == EnumStatus.calc_beg or self.status == EnumStatus.calc_end or self.status == EnumStatus.addframes_end:
                self.status = newStatus
                ret = self.nr

        elif newStatus == EnumStatus.calc_end:
            if self.status == EnumStatus.calc_beg:
                self.status = newStatus
                frameData.countCalc = frameData.countCalc + 1
                ret = self.nr

        elif newStatus == EnumStatus.addframes_beg:
            if self.status == EnumStatus.calc_end:
                self.status = newStatus
                ret = self.nr

        elif newStatus == EnumStatus.addframes_end:
            if self.status == EnumStatus.addframes_beg:
                self.status = newStatus
                frameData.countDraw = frameData.countDraw + 1
                ret = self.nr

        elif newStatus == EnumStatus.web_beg:
            if self.status == EnumStatus.addframes_end:
                self.status = newStatus
                ret = self.nr

        elif newStatus == EnumStatus.web_end:
            if self.status == EnumStatus.web_beg:
                self.status = EnumStatus.empty
                frameData.countWeb = frameData.countWeb + 1
                ret = self.nr

        self.x_lock.release()
        return ret
        


class ImageProcessor():


    @staticmethod
    def ProcessVideoFrame(objFrameData, valueList, videoSource, bgSubtractor):

        nr = objFrameData.SetStatus(EnumStatus.calc_beg)
        if nr == 0:
            return


        # Read video data from camera / video source
        if objFrameData.system == "Windows":
            rc,objFrameData.rawFrame = videoSource.read()
        elif objFrameData.system == "Raspi":
            objFrameData.rawFrame = videoSource.read()

        if objFrameData.rawFrame == None:
            return 1

        # Cut video frame to size of region of interest (roi)
        objFrameData.roiFrame = objFrameData.rawFrame[objFrameData.roiRect.y1 : objFrameData.roiRect.y2, objFrameData.roiRect.x1 : objFrameData.roiRect.x2]

        # Convert roi-frame to gray scale 
        objFrameData.roiFrameGray = cv2.cvtColor(objFrameData.roiFrame, cv2.COLOR_BGR2GRAY)

        # Run background subtraction on gray scale roi-frame
        objFrameData.roiFrameSubtract = bgSubtractor.apply(objFrameData.roiFrameGray)

        # Show the background subtraction of gray scale roi-frame
        #cv2.imshow('Background subtraction', objFrameData.roiFrameSubtract)

        # Run thresholding on subtraction in order to get rid of shadows
        ret, objFrameData.roiFrameSubtract = cv2.threshold(objFrameData.roiFrameSubtract, 150, 255, 0)

        # Show the thresholded background subtraction of gray scale roi-frame
        #cv2.imshow('Background subtraction - thresholded', objFrameData.roiFrameSubtract)

        # Blur subtraction image in order to get coherent contours of the bees
        objFrameData.roiFrameSubtract = cv2.blur(objFrameData.roiFrameSubtract, (10,10))

        # Show the thresholded, blurred background subtraction of gray scale roi-frame
        #cv2.imshow('Background subtraction - blurred', objFrameData.roiFrameSubtract)

        objFrameData.contours = []
        # Get the contours of the subtraction
        im2, objFrameData.contours, hierarchy = cv2.findContours(objFrameData.roiFrameSubtract, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        objFrameData.moments = []
        objFrameData.centers = []

        # Calculate the moments of the contours
        for contour in objFrameData.contours:
            objFrameData.moments.append(cv2.moments(contour))

        # Take those contours which are large enough to be a bee and calculate the coordinates of the corresponding center
        for moment in objFrameData.moments:
            if moment['m00'] > 100:
                objFrameData.centers.append([int(moment['m10']/moment['m00']), int(moment['m01']/moment['m00'])])

        # Calculate the sliding average of the number of detected bees
        valueList["bees"] = ((valueList["bees"] * 1023) / 1024) + (len(objFrameData.centers) / 1024)

        # Calculate the sliding average of the mean value of the roi (indicator for the brightness in the image)
        valueList["light"] = ((valueList["light"] * 1023) / 1024) + (cv2.mean(objFrameData.roiFrameGray)[0] / 1024)

        valueList["imagecount"] = frameData.countCalc
        valueList["webcount"] = frameData.countWeb

        objFrameData.SetStatus(EnumStatus.calc_end)
        
        return 0

    @staticmethod
    def processVideoStream(objFrameData, valueList, videoSource):

        # Initialize the background subtractor
        bgsub_hist = 1000
        bgsub_thresh = 100
        bgSubtractor = cv2.createBackgroundSubtractorMOG2(bgsub_hist, bgsub_thresh, True)

        while True:
            for fdr in objFrameData: 
                if ImageProcessor.ProcessVideoFrame(fdr, valueList, videoSource, bgSubtractor) == 1:
                    break

            ch = 0xFF & cv2.waitKey(5)
            if ch == 27:
                break
            #if objFrameData.system == "Windows":
            #    if ((vidsrc.get(0) >= (args["begin"] + args["length"])) and args["length"] > 0):
            #        break

            #sleep(1/objFrameData.fps)


class ImgThread(threading.Thread): 
  def __init__(self, objFrameData, valueList, videoSource): 
    threading.Thread.__init__(self) 
    self.objFrameData = objFrameData
    self.valueList = valueList
    self.videoSource = videoSource
 
  def run(self): 
    ImageProcessor.processVideoStream(self.objFrameData, self.valueList, self.videoSource)



class DrawImgThread(threading.Thread): 
  def __init__(self, objFrameData, valueList, videoSource): 
    threading.Thread.__init__(self) 
    self.objFrameData = objFrameData
    self.valueList = valueList
    self.videoSource = videoSource
 
  def run(self): 
    while True:
        for fdr in self.objFrameData: 
            nr = fdr.SetStatus(EnumStatus.addframes_beg)
            if nr > 0:
                # Get the raw video frame and convert it to rgb
                fdr.img = cv2.cvtColor(fdr.rawFrame,cv2.COLOR_BGR2RGB)
                    
                # Draw the contours of the found objects into the frame
                cv2.drawContours(fdr.img, fdr.contours, -1, (0,255,0), 1, 8, None, 2, (fdr.roiRect.x1, fdr.roiRect.y1))
                    
                # Draw the region of interest to show where it is in the raw frame
                cv2.rectangle(fdr.img, (fdr.roiRect.x1, fdr.roiRect.y1), (fdr.roiRect.x2, fdr.roiRect.y2), (255, 0, 0))

                # Draw small circles to indicate those contours which are detected as bees
                for center in fdr.centers:
                    cv2.circle(fdr.img, (fdr.roiRect.x1 + center[0], fdr.roiRect.y1 + center[1]), 2, (255,255,255), -1) 


                fdr.SetStatus(EnumStatus.addframes_end)
