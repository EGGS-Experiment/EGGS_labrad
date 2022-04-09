"""
Simple socket client using threads.
"""
import sys
import socket
from os import environ

HOST = environ['LABRADHOST']
PORT = 5500 #environ['EGGS_LABRAD_PORT']
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created.')

# connect socket to desired host and port
try:
    s.connect((HOST, PORT))
except socket.error as msg:
    print('Connect failed. Error Code : ' + str(msg[0]) + '. Message: ' + msg[1])
    sys.exit()
print('Socket connect complete.')

# talk with client
s.sendall(b'Hello world')
s.close()
