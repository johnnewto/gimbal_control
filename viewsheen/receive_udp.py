'''
Receive UDP at the drone from the ground station
'''
import socket

if __name__ == '__main__':

    UDP_IP = "10.5.0.2"   # Drone receive
    UDP_PORT = 1234
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    i = 0
    count = 0
    while True:
        rcv = sock.recv(4096, )
        print (i, rcv)
        i += 1
