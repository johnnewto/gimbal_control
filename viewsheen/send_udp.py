'''
Send UDP to the drone fm the ground station
'''
import socket, time

if __name__ == '__main__':
    # UDP_IP = "127.0.0.1"
    UDP_IP = "10.5.0.2"   # send to drone from the GS
    UDP_PORT = 1234
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    i = 0
    while True:
        sock.sendto(b"Take Screen Shot", (UDP_IP, UDP_PORT))
        print (f"send {i}")
        i += 1
        i = i % 255
        time.sleep(0.5)