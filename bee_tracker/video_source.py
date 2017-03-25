try:
    from imutils.video.pivideostream import PiVideoStream
    from imutils.video import FPS
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError:
    import cv2

class VideoSource():
    
    @staticmethod
    def createVideoStream(system, source, fps, resx, resy, begin):

        try:                                    # Camera as source
            source = int(source)

            if system == "Windows":
                vs =  cv2.VideoCapture(source)
                vs.set(3, resx)                 # Set resolution x (3 = CV_CAP_PROP_FRAME_WIDTH)
                vs.set(4, resy)                 # Set resolution y (4 = CV_CAP_PROP_FRAME_HEIGHT)
                vs.set(5, fps)                  # Set frame rate (5 = CV_CAP_PROP_FPS )

                cv2.ocl.setUseOpenCL(False)     # Necessary to avoid background subtraction errors

            elif system == "Raspi":
                vs = PiVideoStream((resx, resy), fps).start()

        except ValueError:                      # Video as source
            vs =  cv2.VideoCapture(source)
            vs.set(0, begin)                    # Set start of video in ms (0 = CV_CAP_PROP_POS_MSEC)
            
            if system == "Windows":
                cv2.ocl.setUseOpenCL(False)     # Necessary to avoid background subtraction errors

        return vs

