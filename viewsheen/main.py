import cv2, time
from imutils import resize
from gimbal_cntrl import pan_tilt, VS_IP_ADDRESS, VS_PORT
import socket

# Create a VideoCapture object to read from the RTSP stream
# rtsp_url = 'rtsp://admin:camera21@192.168.0.3:554/h264Preview_01_main'
# rtsp_url = 'rtsp://admin:camera21@192.168.0.3:554/h264Preview_01_sub'
# rtsp_url = 'rtsp://admin:admin@192.168.42.108:554/cam/realmonitor?channel=1&subtype=0'

# rtsp_url = 'rtsp://192.168.144.25:8554/main.264'     # siyi ip camera perhaps?
def main():
    rtsp_url   = 'rtsp://admin:admin@192.168.144.108:554/cam/realmonitor?channel=1&subtype=0'       # viewsheen ip camera

    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to viewsheen gimbal
    sock.connect((VS_IP_ADDRESS, VS_PORT))

    cap = cv2.VideoCapture(rtsp_url)
    cv2.namedWindow('RTSP', cv2.WINDOW_NORMAL)
    # Check if the VideoCapture object was successfully created
    if not cap.isOpened():
        print('Failed to open RTSP stream')
        exit()

    print('Opened RTSP stream')
    # Loop through the frames of the RTSP stream
    gimbal_speed = 80
    while True:
        # Read a frame from the RTSP stream
        ret, frame = cap.read()

        # Check if the frame was successfully read
        if not ret:
            print('Failed to read frame from RTSP stream')
            break

        # Display the frame
        # frame = resize(frame, width=1000)
        # [row, col, z] = frame.shape
        # frame = frame[row//2-100:row//2+100,  col//2-100:col//2+100]
        cv2.imshow('RTSP', frame)

        key = cv2.waitKey(1)

        if key == ord('q') or key == 27:
            # Exit the program if the user presses the 'q' key
            break
        if key == ord('d'):  # Right arrow key
            print("Right arrow key pressed")
            data = pan_tilt(gimbal_speed)
            sock.sendall(data)
            time.sleep(0.5)
        if key == ord('a'):  # Left arrow key
            print("Left arrow key pressed")
            data = pan_tilt(-gimbal_speed)
            sock.sendall(data)
            time.sleep(0.5)
        if key == ord('w'):
            print("Up arrow key pressed")
            data = pan_tilt(0, gimbal_speed)
            sock.sendall(data)
            time.sleep(0.5)
        if key == ord('s'):
            print("Down arrow key pressed")
            data = pan_tilt(0, -gimbal_speed)
            sock.sendall(data)
            time.sleep(0.5)
    # Close the socket
    sock.close()
    # Release the VideoCapture object and close the display window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()