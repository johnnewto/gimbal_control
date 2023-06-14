#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet import reactor, defer
from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import HostnameEndpoint
from twisted.internet.protocol import ClientFactory, ReconnectingClientFactory, Factory
from twisted.protocols.basic import LineReceiver
from viewsheen import gimbal_cntrl
from viewsheen import GST_Video
import cv2, time
import numpy as np
from pynput import keyboard, mouse

GIMBAL_SPEED = 50

class EchoClient(LineReceiver):
    end = b"Bye-bye!"

    def connectionMade(self):
        print("connection made")

    def lineReceived(self, line):
        print("receive:", line)
        if line == self.end:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        pass

_loopCounter = 0
def runEverySecond(data):
    global _loopCounter
    _loopCounter += 1
    # print('A new second has passed.', data, _loopCounter)
    return

last_key = None
data = None
def control_gimbal(protocol, video):
    global _loopCounter, last_key, data
    # get image from another thread
    if video.frame_available():
        frame = video.frame().copy()
        cv2.imshow('RTSP Stream', frame)

    key = cv2.waitKey(1)
    # data = None
    if key != -1:
        print(key)
        last_key = key
    if key == ord('q') or key == 27:
        reactor.stop()
    if key == ord('d'):  # Right arrow key
        print("Right arrow key pressed")
        data = gimbal_cntrl.pan_tilt(GIMBAL_SPEED)

    elif key == ord('a'):  # Left arrow key
        print("Left arrow key pressed")
        data = gimbal_cntrl.pan_tilt(-GIMBAL_SPEED)

    elif key == ord('w'):
        print("Up arrow key pressed")
        data = gimbal_cntrl.pan_tilt(0, GIMBAL_SPEED)


    elif key == ord('s'):
        print("Down arrow key pressed")
        data = gimbal_cntrl.pan_tilt(0, -GIMBAL_SPEED)

    if last_key is not None and data is not None:
        print("resending data")
        # data = gimbal_cntrl.pan_tilt(protocol.gimbal_speed)
        protocol.transport.write(data)

def connected(protocol, video):
    # protocol is an instance of EchoClient and is connected
    cv2.namedWindow('RTSP Stream', cv2.WINDOW_NORMAL)
    print('Initialising stream...')
    waited = 0
    while not video.frame_available():
        waited += 1
        print('\r  Frame not available (x{})'.format(waited), end='')
        cv2.waitKey(30)

    print('\nSuccess!\nStarting streaming - press "q" to quit.')

    return task.LoopingCall(control_gimbal, protocol, video).start(0.05)

# def control_gimbal():
#

def main():

    VS_IP_ADDRESS = '192.168.144.200'
    VS_PORT = 2000
    ep = HostnameEndpoint(reactor, VS_IP_ADDRESS, VS_PORT)
    d = ep.connect(Factory.forProtocol(EchoClient))
    video = GST_Video.GST_Video()
    d.addCallback(connected, video)
    return d

def on_key_release(key):
    global last_key
    print("key released", key)
    last_key = None

def on_key_press(key):
    pass
    # global last_key
    # print("key pressed", key)
    # last_key = key

if __name__ == "__main__":
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    keyboard.Listener(on_press=on_key_press, on_release=on_key_release).start()
    # self.key_listener.start()
    task.LoopingCall(runEverySecond, 'hello').start(1)
    reactor.callWhenRunning(main)

    reactor.run()