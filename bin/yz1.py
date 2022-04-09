"""
Simple socket server using threads.
"""
import socket
import sys
from os import environ

HOST = environ['LABRADHOST']
PORT = 5500 #environ['EGGS_LABRAD_PORT']
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

# Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()
print('Socket bind complete')
# Start listening on socket
s.listen(10)
print('Socket now listening')

# now keep talking with the client
while 1:
    # wait to accept a connection - blocking call
    conn, addr = s.accept()
    print('Connected with ' + addr[0] + ':' + str(addr[1]))
    with conn:
        while True:
            data = conn.recv(1024)
            print(data)
            if not data:
                break
            conn.sendall(data)

s.close()
