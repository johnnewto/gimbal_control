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
import PySimpleGUI as sg
from gimbal_cntrl import pan_tilt, snapshot, zoom, VS_IP_ADDRESS, VS_PORT, KeyReleaseThread, yaw, pitch
import gimbal_cntrl as gimbal

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
# Class holding the button graphic info. At this time only the state is kept
class BtnInfo:
    def __init__(self, state=True):
        self.state = state        # Can have 3 states - True, False, None (disabled)

def gui():
    sg.theme('LightGreen')

    # define the window layout
    layout = [
      [sg.Text('OpenCV Demo', size=(60, 1), justification='center')],
      # [sg.Image(filename='', key='-IMAGE-')],
      [sg.Button('Toggle', size=(10, 1), k='-TOGGLE1-', border_width=0, button_color='white on green', metadata=BtnInfo())],
      [sg.Button('Forward', size=(10, 1)), sg.Button('Down', size=(10, 1)), sg.Button('Snap', size=(10, 1)), sg.Button('Record', size=(10, 1), button_color='white on green'),],
      [sg.Button('Yaw', size=(10, 1)), sg.Slider((0, 360), 180, 1, orientation='h', size=(40, 15), key='-YAW-', enable_events = True)],
      [sg.Button('Pitch', size=(10, 1)), sg.Slider((-100, 60), 0, 1, orientation='h', size=(40, 15), key='-PITCH-', enable_events=True)],
      [sg.Radio('None', 'Radio', True, size=(10, 1))],
      [sg.Radio('threshold', 'Radio', size=(10, 1), key='-THRESH-'),
       sg.Slider((0, 255), 128, 1, orientation='h', size=(40, 15), key='-THRESH SLIDER-')],
      [sg.Radio('canny', 'Radio', size=(10, 1), key='-CANNY-'),
       sg.Slider((0, 255), 128, 1, orientation='h', size=(20, 15), key='-CANNY SLIDER A-'),
       sg.Slider((0, 255), 128, 1, orientation='h', size=(20, 15), key='-CANNY SLIDER B-')],
      [sg.Radio('blur', 'Radio', size=(10, 1), key='-BLUR-'),
       sg.Slider((1, 11), 1, 1, orientation='h', size=(40, 15), key='-BLUR SLIDER-')],
      [sg.Radio('hue', 'Radio', size=(10, 1), key='-HUE-'),
       sg.Slider((0, 225), 0, 1, orientation='h', size=(40, 15), key='-HUE SLIDER-')],
      [sg.Radio('enhance', 'Radio', size=(10, 1), key='-ENHANCE-'),
       sg.Slider((1, 255), 128, 1, orientation='h', size=(40, 15), key='-ENHANCE SLIDER-')],

      [sg.Text()],
      [sg.Text('           '),sg.RealtimeButton(sg.SYMBOL_UP, key='-GIMBAL-UP-')],
      [sg.RealtimeButton(sg.SYMBOL_LEFT, key='-GIMBAL-LEFT-'), sg.Text(size=(10,1), key='-STATUS-', justification='c', pad=(0,0)),
       sg.RealtimeButton(sg.SYMBOL_RIGHT, key='-GIMBAL-RIGHT-')],
      [sg.Text('           '), sg.RealtimeButton(sg.SYMBOL_DOWN, key='-GIMBAL-DOWN-')],[sg.Text()],
      [sg.Button('Hide', size=(10, 1)), sg.Column([[sg.Button('Exit', size=(10, 1))]], justification='r')],
    ]

    # create the window and show it without the plot
    return sg.Window('OpenCV Integration', layout, location=(800, 400))

def process_frame(frame, values):
    if values['-THRESH-']:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)[:, :, 0]
        frame = cv2.threshold(frame, values['-THRESH SLIDER-'], 255, cv2.THRESH_BINARY)[1]
    elif values['-CANNY-']:
        frame = cv2.Canny(frame, values['-CANNY SLIDER A-'], values['-CANNY SLIDER B-'])
    elif values['-BLUR-']:
        frame = cv2.GaussianBlur(frame, (21, 21), values['-BLUR SLIDER-'])
    elif values['-HUE-']:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame[:, :, 0] += int(values['-HUE SLIDER-'])
        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
    elif values['-ENHANCE-']:
        enh_val = values['-ENHANCE SLIDER-'] / 40
        clahe = cv2.createCLAHE(clipLimit=enh_val, tileGridSize=(8, 8))
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return frame

# Define a function repeat under timer
def timer(window, arg):
   print('win lift')
   window.TKroot.after(1000, timer, arg)

def main(sock=None):

    window = gui()
    window.Finalize()
    # Make the window jump above all
    # window.TKroot.attributes('-topmost', True)
    # window.keep_on_top_set()
    window.bind('d', '-GIMBAL-RIGHT-')


    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO | cv2.WINDOW_GUI_EXPANDED)

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
    gimbal_key = None
    # event loop
    while True:
        if video.frame_available():
            frame = video.frame().copy()
        else:
            frame = None

        key = cv2.waitKey(1)
        if key != -1:
            window.keep_on_top_clear()

        event, values = window.read(timeout=50)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event in ('Hide'):
            window.hide()
        if 'TOGGLE' in event:
            window[event].metadata.state = not window[event].metadata.state

        if event in (['Yaw']):
            yaw_val = values['-YAW-']
            print ('Yaw', yaw_val)
            data = gimbal.yaw(yaw_val)
            print(data[15:])
            sock.sendall(data)


        if event in (['Pitch']):
            pitch_val = values['-PITCH-']
            print ('Pitch', pitch_val)
            data = gimbal.pitch(pitch_val)
            print(data[15:])
            sock.sendall(data)

        if event in (['Forward']):
            key = ord('f')

        if event in (['Down']):
            key = ord('v')
        # if event in ('-UP-', '-LEFT-', '-RIGHT-', '-DOWN-'):
        if 'GIMBAL' in event:
            # if not a timeout event, then it's a button that's being held down
            window['-STATUS-'].update(event)
            if gimbal_key is None:
                if event in ('-GIMBAL-UP-'):
                    gimbal_key = key = ord('w')

                if event in ('-GIMBAL-DOWN-'):
                    gimbal_key = key = ord('s')

                if event in ('-GIMBAL-LEFT-'):
                    gimbal_key = key = ord('a')

                if event in ('-GIMBAL-RIGHT-'):
                    gimbal_key = key = ord('d')

        else:
            # A timeout signals that all buttons have been released so clear the status display
            window['-STATUS-'].update('')
            if gimbal_key is not None:
                gimbal_key = None


        if frame is not None:
            frame = process_frame(frame, values)

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


        if key == ord('q') or key == ord('Q') or key == 27:
            break

        if key == ord('d'):  # Right arrow key
            print("Right arrow key pressed")
            data = pan_tilt(gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('a'):  # Left arrow key
            print("Left arrow key pressed")
            data = pan_tilt(-gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('w'):
            print("Up arrow key pressed")
            data = pan_tilt(0, gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('s'):
            print("Down arrow key pressed")
            data = pan_tilt(0, -gimbal_speed)
            KeyReleaseThread(sock, data).start()

        if key == ord('1'):
            print("Zoom in pressed")
            data = zoom(1)
            sock.sendall(data)

        if key == ord('2'):
            print("Zoom out pressed")
            data = zoom(2)
            sock.sendall(data)

        if key == ord('3'):
            print("Zoom stop pressed")
            data = zoom(2)
            sock.sendall(data)

        if key == ord('4'):
            print("Zoom  = 1")
            data = zoom(4)
            sock.sendall(data)

        if key == ord('5'):
            print("Zoom x2 in")
            data = zoom(5)
            sock.sendall(data)

        if key == ord('6'):
            print("Zoom x2 out")
            data = zoom(6)
            sock.sendall(data)

        if key == ord('c'):
            print("Snapshot pressed")
            data = snapshot(1, 0)
            KeyReleaseThread(sock, data).start()

        if key == ord('m'):
            print("Menu pressed")
            window.keep_on_top_set()
            window.un_hide()

        if key == ord('v'):
            print("down pressed")
            data = gimbal.oneKeyDown()
            print(data)
            sock.sendall(data)

        if key == ord('f'):
            print("forward pressed")
            data = gimbal.forward()
            print(data)
            sock.sendall(data)

        # if key == ord('h'):
        #     print("quickCalibration in pressed")
        #     data = gimbal.quickCalibration()
        #     print(data)
        #     sock.sendall(data)

        # if key == ord('t'):
        #     print("trackingStop pressed")
        #     data = gimbal.trackingStop()
        #     print(data)
        #     sock.sendall(data)

            # KeyReleaseThread(sock, data).start()
"""
Test with :
"""

if __name__ == '__main__':

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to viewsheen gimbal
    sock.connect((VS_IP_ADDRESS, VS_PORT))

    main(sock)
    sock.close()
    cv2.destroyAllWindows()