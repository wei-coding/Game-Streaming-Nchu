#!/usr/bin/env python

from __future__ import division
import cv2
import numpy as np
import socket
import struct
import math
import time
import threading
#import pyautogui as pg
from mss import mss
from PIL import Image
from Protocol import *


class FrameSegment(threading.Thread):
    """
    Object to break down image frame segment
    if the size of image exceed maximum datagram size
    """
    MAX_DGRAM = 2**16 - 64
    MAX_IMAGE_DGRAM = MAX_DGRAM - 64  # extract 64 bytes in case UDP frame overflown
    ENCODE_PARAM_JPEG = [int(cv2.IMWRITE_JPEG_QUALITY),60,int(cv2.IMWRITE_JPEG_PROGRESSIVE),0,int(cv2.IMWRITE_JPEG_OPTIMIZE),1]
    ENCODE_PARAM_PNG = [int(cv2.IMWRITE_PNG_COMPRESSION), 7]
    ENCODE_PARAM_WEBP = [int(cv2.IMWRITE_WEBP_QUALITY), 101]
    def __init__(self, sock, port, addr="192.168.0.103"):
        threading.Thread.__init__(self)
        self.s = sock
        self.port = port
        self.addr = addr
        self.buffer = []
        self.signal = True
        self.datagram_builder = DatagramBuilder()
        self.seq = -1

    def run(self):
        """
        Compress image and Break down
        into data segments
        """
        while self.signal:
            if(len(self.buffer) != 0):
                img = self.buffer.pop()
                compress_img = cv2.imencode('.jpg', img, self.ENCODE_PARAM_JPEG)[1]
                dat = compress_img.tostring()
                size = len(dat)
                count = math.ceil(size/(self.MAX_IMAGE_DGRAM))
                array_pos_start = 0
                raw_data = b''
                while count:
                    self.seq += 1
                    self.seq %= 1024
                    array_pos_end = min(size, array_pos_start + self.MAX_IMAGE_DGRAM)
                    now = time.time()
                    send_data = self.datagram_builder.pack(self.seq,True if count == 1 else False,int((now - int(now)) * 1000000)) + dat[array_pos_start:array_pos_end]
                    self.s.sendto(send_data, (self.addr, self.port))
                    array_pos_start = array_pos_end
                    count -= 1
                    #time.sleep(10)
            else:
                print("Sleeping...")
                time.sleep(0.1)
    def add_buffer(self,img):
        if(len(self.buffer) >= 10):
            time.sleep(1)
            return
        self.buffer.insert(0,img)
        print(len(self.buffer))
    def stop(self):
        self.signal = False
class ScreenShot(threading.Thread):
    def __init__(self,fs_,w_=1920,h_=1080):
        threading.Thread.__init__(self)
        self.w = w_
        self.h = h_
        self.sct = mss()
        self.fs = fs_
        self.signal = True
    def run(self):
        mon = {'top':0,'left':0,'width':self.w,'height':self.h}
        while self.signal:
            sct_img = self.sct.grab(mon)
            img = Image.frombytes('RGB',sct_img.size,sct_img.bgra,'raw','BGRX')
            img = cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
            self.fs.add_buffer(img)
    def stop(self):
        self.signal = False
def main():
    """ Top level main function """
    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 12345

    fs = FrameSegment(s, port)
    #(w,h) = pg.size()
    ss = ScreenShot(fs)
    ss.start()
    fs.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        fs.stop()
        ss.stop()
    s.close()


if __name__ == "__main__":
    main()
