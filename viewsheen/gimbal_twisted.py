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
import cv2, time
import numpy as np
from pynput import keyboard, mouse



class EchoClient(LineReceiver):
    end = b"Bye-bye!"
    gimbal_speed = 50

    def connectionMade(self):
        data = gimbal_cntrl.pan_tilt(self.gimbal_speed)
        # self.sendLine(data)
        self.transport.write(data)


    def lineReceived(self, line):
        print("receive:", line)
        if line == self.end:
            self.transport.loseConnection()

    def sendData(self):
        data = gimbal_cntrl.pan_tilt(self.gimbal_speed)
        self.sendLine(data)

_loopCounter = 0
def runEverySecond(data):
    """
    Called at ever loop interval.
    """
    global _loopCounter
    _loopCounter += 1
    # print('A new second has passed.', data, _loopCounter)
    return

last_key = None
data = None
def sendData(protocol):
    global _loopCounter, last_key, data
    # get image from another thread
    cv2.imshow('RTSP Stream', np.zeros((50, 100, 3), 'uint8'))
    key = cv2.waitKey(50)
    # data = None
    if key != -1:
        print(key)
        last_key = key

    if key == ord('d'):  # Right arrow key
        print("Right arrow key pressed")
        data = gimbal_cntrl.pan_tilt(protocol.gimbal_speed)

    elif key == ord('a'):  # Left arrow key
        print("Left arrow key pressed")
        data = gimbal_cntrl.pan_tilt(-protocol.gimbal_speed)

    elif key == ord('w'):
        print("Up arrow key pressed")
        data = gimbal_cntrl.pan_tilt(0, protocol.gimbal_speed)


    elif key == ord('s'):
        print("Down arrow key pressed")
        data = gimbal_cntrl.pan_tilt(0, -protocol.gimbal_speed)

    if last_key is not None and data is not None:
        print("resending data")
        # data = gimbal_cntrl.pan_tilt(protocol.gimbal_speed)
        protocol.transport.write(data)

def connected(protocol):
    # protocol is an instance of EchoClient and is connected
    return task.LoopingCall(sendData, protocol).start(0.001)


def main():

    VS_IP_ADDRESS = '192.168.144.200'
    VS_PORT = 2000
    ep = HostnameEndpoint(reactor, VS_IP_ADDRESS, VS_PORT)
    d = ep.connect(Factory.forProtocol(EchoClient))
    d.addCallback(connected)
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