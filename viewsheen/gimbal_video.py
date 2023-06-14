#!/usr/bin/env python
"""
viewsheen gimbal control

"""

import cv2


from viewsheen import GST_Video

import datetime

from pathlib import Path



def main(sock=None):


    cv2.namedWindow('Receive', cv2.WINDOW_NORMAL)

    # threading.Thread(target=socket_function, args=('10.42.0.1',1234), daemon=True).start()
    # threading.Thread(target=socket_function, args=('127.0.0.1',9000), daemon=True).start()

    video = GST_Video.GST_Video()



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