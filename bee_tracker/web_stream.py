from __future__ import division

import cv2
import PIL as pillow
import threading
import StringIO
import time
import socket

from PIL import Image
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
from image_processor import frameData
from image_processor import EnumStatus
from image_processor import roiRectangle

class CamHandler(BaseHTTPRequestHandler):

    def processImage(self, fdr):

        nr = fdr.SetStatus(EnumStatus.web_beg)
        if nr == 0:
            return

        #dieser Teil koennte vom DrawImgThread erledigt werden {


        # Get the raw video frame and convert it to rgb
        fdr.img = cv2.cvtColor(fdr.rawFrame,cv2.COLOR_BGR2RGB)
                    
        # Draw the contours of the found objects into the frame
        cv2.drawContours(fdr.img, fdr.contours, -1, (0,255,0), 1, 8, None, 2, (fdr.roiRect.x1, fdr.roiRect.y1))
                    
        # Draw the region of interest to show where it is in the raw frame
        cv2.rectangle(fdr.img, (fdr.roiRect.x1, fdr.roiRect.y1), (fdr.roiRect.x2, fdr.roiRect.y2), (255, 0, 0))

        # Draw small circles to indicate those contours which are detected as bees
        for center in fdr.centers:
            cv2.circle(fdr.img, (fdr.roiRect.x1 + center[0], fdr.roiRect.y1 + center[1]), 2, (255,255,255), -1) 

        #dieser Teil koennte vom DrawImgThread erledigt werden }


        jpg = Image.fromarray( fdr.img)
        tmpFile = StringIO.StringIO()
        jpg.save(tmpFile,'JPEG')

        self.wfile.write("--jpgboundary")
        self.send_header('Content-type','image/jpeg')
        self.send_header('Content-length',str(tmpFile.len))
        self.end_headers()
        self.wfile.write( tmpFile.getvalue() )
        
        #time.sleep(1/fdrRef[0].fps)

        fdr.countWeb = fdr.countWeb + 1
        fdr.SetStatus(EnumStatus.web_end)

    def do_GET(self):

        if self.path.endswith('.mjpg'):

            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()

            while True:
                try:
                    for fdr in frameDataRef: 
                        CamHandler.processImage(self, fdr)
 
                    if frameData.terminateWebThread == 1:
                        break;

                except KeyboardInterrupt:
                    break
            return

        if self.path.endswith('.html'):

            self.send_response(200)
            self.send_header('content-type','text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="http://' + ip + ':8080/cam.mjpg"/>')
            self.wfile.write('</body></html>')

            return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def get_ip_address():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("192.168.2.1", 80))

    return s.getsockname()[0]

class WebcamServerThread(threading.Thread):

    def __init__(self, args, frameData):

        threading.Thread.__init__(self)
        
        global frameDataRef
        frameDataRef = frameData

    def run(self):

        try:
            global ip
            ip = get_ip_address()
            print(ip)
            
            server = ThreadedHTTPServer((ip, 8080), CamHandler)
            
            print "server started"
            server.serve_forever()

            

        except KeyboardInterrupt:
            capture.release()
            server.socket.close()
            