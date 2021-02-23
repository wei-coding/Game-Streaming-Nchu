#!/usr/bin/env python

from __future__ import division
import cv2
import socket
import time
import threading
import win32gui
import numpy as np
import screenshot
import d3dshot
from FpsMeter import *
from FrameSegment import *

def main(hwnd):
    """ Top level main function """
    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 12345
    fs = FrameSegment(s, port)
    fs.start()
    fm = FpsMeter(interval=5)
    fm.start()
    ss = screenshot.gpu_screenshots()
    while True:
        try:
            #img = screenshot.background_screenshot(hwnd)
            img = ss.get_frames()
            print(img)
            img = cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
            fs.add_buffer(img)
            fm.inc_count()
            print('successed')
        except Exception:
            print('can\'t find window')
            continue
        #print('screenshot successed.')
        
    s.close()


if __name__ == "__main__":
    main(win32gui.FindWindow(None, '控制台'))
