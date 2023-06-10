#!/usr/bin/env python
"""
Gstreamer video capture
https://www.ardusub.com/developers/opencv.html
"""
import socket
import time

import cv2
import gi
import numpy as np


gi.require_version('Gst', '1.0')
from gi.repository import Gst


import datetime

from pathlib import Path


class FPS:
    def __init__(self):
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self._start = None
        self._end = None
        self._numFrames = 0

    def start(self):
        # start the timer
        self._start = datetime.datetime.now()
        return self

    def stop(self):
        # stop the timer
        self._end = datetime.datetime.now()

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self._numFrames += 1

    def elapsed(self):
        # return the total number of seconds between the start and
        # end interval
        return (self._end - self._start).total_seconds()

    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()


# dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_1000)
# # Initialize the detector parameters using default values
# parameters = cv2.aruco.DetectorParameters_create()


class Video():
    """BlueRov video capture class constructor

    Attributes:
        port (int): Video UDP port
        video_codec (string): Source h264 parser
        video_decode (string): Transform YUV (12bits) to BGR (24bits)
        video_pipe (object): GStreamer top-level pipeline
        video_sink (object): Gstreamer sink element
        video_sink_conf (string): Sink configuration
        video_source (string): Udp source ip and port
        latest_frame (np.ndarray): Latest retrieved video frame
    """

    def __init__(self, address='127.0.0.1', port=1234, code_patch_size=100):
        """Summary
        Args:
            port (int, optional): UDP port
        """

        Gst.init(None)

        self.address = address
        self.port = port
        self.code_patch_size = code_patch_size

        self.latest_frame = self._new_frame = None

        # [Software component diagram](https://www.ardusub.com/software/components.html)
        # UDP video stream (:5600)
        # self.video_source = f'udpsrc address={address} port={port}'
        self.video_source = f'rtspsrc location=rtsp://admin:admin@192.168.144.108:554 latency=100 ! queue'
        # self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264'
        self.video_codec = '! rtph264depay ! h264parse ! avdec_h264'
        # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        self.video_decode = '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert'
        # Create a sink to get data
        self.video_sink_conf = '! appsink emit-signals=true sync=false max-buffers=2 drop=true'

        self.video_pipe = None
        self.video_sink = None
        self.pause = False
        self.run()

    def start_gst(self, config=None):
        """ Start gstreamer pipeline and sink
        Pipeline description list e.g:
            [
                'videotestsrc ! decodebin', \
                '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                '! appsink'
            ]

        Args:
            config (list, optional): Gstreamer pileline description list
        """

        if not config:
            config = \
                [
                    'videotestsrc ! decodebin',
                    '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                    '! appsink'
                ]

        command = ' '.join(config)
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_opencv(sample):
        """Transform byte array into np array
        Args:q
            sample (TYPE): Description
        Returns:
            TYPE: Description
        """
        buf = sample.get_buffer()
        caps_structure = sample.get_caps().get_structure(0)
        array = np.ndarray(
            (
                caps_structure.get_value('height'),
                caps_structure.get_value('width'),
                3
            ),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def frame(self):
        """ Get Frame

        Returns:
            np.ndarray: latest retrieved image frame
        """
        if self.frame_available:
            self.latest_frame = self._new_frame
            # reset to indicate latest frame has been 'consumed'
            self._new_frame = None
        return self.latest_frame

    def frame_available(self):
        """Check if a new frame is available

        Returns:
            bool: true if a new frame is available
        """
        return self._new_frame is not None

    def run(self):
        """ Get frame to update _new_frame
        """

        self.start_gst(
            [
                self.video_source,
                self.video_codec,
                self.video_decode,
                self.video_sink_conf
            ])

        self.video_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        # if not self.pause:
        self._new_frame = self.gst_to_opencv(sample)

        return Gst.FlowReturn.OK


data_received = ''


def socket_function(address, port):
    global data_received
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP

    sock.bind((address, port))

    while True:
        data_received = sock.recv(4096, )
        data_received = str(data_received)[2:-1]  # get rid of b/'.....'
        pass


def main(sock=None):


    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL)

    # threading.Thread(target=socket_function, args=('10.42.0.1',1234), daemon=True).start()
    # threading.Thread(target=socket_function, args=('127.0.0.1',9000), daemon=True).start()

    video = Video()



    print('Initialising stream...')
    waited = 0
    while not video.frame_available():
        waited += 1
        print('\r  Frame not available (x{})'.format(waited), end='')
        cv2.waitKey(30)

    print('\nSuccess!\nStarting streaming - press "q" to quit.')

    gimbal_speed = 40
    while True:

        if video.frame_available():
            frame = video.frame().copy()




            # frame = resize(frame, width=4000)
            # r, c, _ = frame.shape
            # p = (np.array(params.pos)*(r,r,c,c)).astype(int)
            # frame = frame[p[0]:p[1], p[2]:p[3]]

            # print(codes, diffs)
            # print (f"Mean value received = {code0/16:.1f}  {code1/16:.1f} ")
            # cv2.putText(frame, f'Rx: {codes}', (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 15)
            # cv2.imshow('Receive', frame[1900:2200, 1920:2220])

            # shp = frame.shape

            # cv2.putText(frame, f'fps={params.fps}  bitrate={params.bitrate} Kbits/s', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
            # cv2.putText(frame, f'{frame_num:2d} {data_received}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
            cv2.imshow('Receive', frame)

        k = cv2.waitKey(1)
        if k == ord('q') or k == ord('Q') or k == 27:
            break

        if k == ord('d'):  # Right arrow key
            print("Right arrow key pressed")
            data = pan_tilt(gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if k == ord('a'):  # Left arrow key
            print("Left arrow key pressed")
            data = pan_tilt(-gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if k == ord('w'):
            print("Up arrow key pressed")
            data = pan_tilt(0, gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if k == ord('s'):
            print("Down arrow key pressed")
            data = pan_tilt(0, -gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if k == ord('1'):
            print("Zoom in pressed")
            data = zoom(1)
            sock.sendall(data)

        if k == ord('2'):
            print("Zoom out pressed")
            data = zoom(2)
            sock.sendall(data)

        if k == ord('3'):
            print("Zoom stop pressed")
            data = zoom(2)
            sock.sendall(data)

        if k == ord('4'):
            print("Zoom  = 1")
            data = zoom(4)
            sock.sendall(data)

        if k == ord('5'):
            print("Zoom x2 in")
            data = zoom(5)
            sock.sendall(data)

        if k == ord('6'):
            print("Zoom x2 out")
            data = zoom(6)
            sock.sendall(data)

        if k == ord('c'):
            print("Snapshot in pressed")
            data = snapshot(1, 0)
            KeyReleaseThread(sock, data).start()

            # KeyReleaseThread(sock, data).start()
"""
Test with :

gst-launch-1.0 -v filesrc location=~/Videos/Big_Buck_Bunny_720_10s_2MB.mp4 ! decodebin ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=1234

gst-launch-1.0 -v filesrc location=~/Videos/paragliders-1.mp4 ! decodebin ! x264enc             ! rtph264pay ! udpsink host=127.0.0.1 port=1234
gst-launch-1.0 -v filesrc location=~/Videos/paragliders-1.mp4 ! decodebin ! x264enc bitrate=300 ! rtph264pay ! udpsink host=127.0.0.1 port=1234
 
gst-launch-1.0 -v videotestsrc ! x264enc             ! rtph264pay ! udpsink host=127.0.0.1 port=1235

gst-launch-1.0 -v videotestsrc ! x264enc bitrate=2048 ! rtph264pay ! udpsink host=127.0.0.1 port=1235
gst-launch-1.0 -v videotestsrc ! video/x-raw,format=BGR,width=640,height=480 ! x264enc bitrate=2048! rtph264pay ! udpsink host=127.0.0.1 port=1235
experimental:
#    out = cv2.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency noise-reduction=10000 bitrate=2048 speed-preset=superfast ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=5000',
# 
#    format=BGR,width=640,height=480,framerate=20/1
#    gst_str_rtp = "appsrc ! queue ! videoconvert ! video/x-raw ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=1234"
# 
#    appsrc name=source is-live=true block=true format=GST_FORMAT_TIME " \
#                     " caps=video/x-raw,format=BGR,width=640,height=480,framerate={}/1 " \
#                     "! videoconvert ! video/x-raw,format=I420 "
# 
#                     video/x-raw,format=BGR,width=640,height=480,framerate={}/1
# 
# gst-launch-1.0 -v videotestsrc ! video/x-raw,format=BGR,width=640,height=480 ! x264enc bitrate=2048! rtph264pay ! udpsink host=127.0.0.1 port=1234
# gst-launch-1.0 -v videotestsrc ! x264enc format=BGR,width=640,height=480 ! rtph264pay ! udpsink host=127.0.0.1 port=1234
"""

if __name__ == '__main__':
    from gimbal_cntrl import pan_tilt, snapshot,  zoom, VS_IP_ADDRESS, VS_PORT, KeyReleaseThread
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to viewsheen gimbal
    sock.connect((VS_IP_ADDRESS, VS_PORT))

    main(sock)
    sock.close()
    cv2.destroyAllWindows()