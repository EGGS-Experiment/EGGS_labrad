#!/usr/bin/env python

## Tiny Syslog Server in Python.
##
## This is a tiny syslog server that is able to receive UDP based syslog
## entries on a specified port and save them to a file.
## That's it... it does nothing else...
## There are a few configuration parameters.

# get labrad syslog socket
from os import environ
HOST, PORT = "localhost", int(environ["EGGS_LABRAD_SYSLOG_PORT"])

# format date for filename
from datetime import datetime
date = datetime.now()
trunk1 = '{0:d}_{1:02d}_{2:02d}_{3:02d}{4:02d}'.format(date.year, date.month, date.day, date.hour, date.minute)
LOG_FILE = 'C:\\Users\\EGGS1\\Documents\\.labrad\\logfiles\\{0:s}.log'.format(trunk1)

#
# NO USER SERVICEABLE PARTS BELOW HERE...
#

import logging
import socketserver

logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='', filename=LOG_FILE, filemode='a')


class SyslogUDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        socket = self.request[1]
        print("%s : " % self.client_address[0], str(data))
        logging.info(str(data))


if __name__ == "__main__":
    print("LabRAD SysLog: starting up ...")
    try:
        server = socketserver.UDPServer((HOST, PORT), SyslogUDPHandler)
        print("LabRAD SysLog: startup successful.")
        print("LabRAD SysLog: Now serving @ {:s}:{:d}.".format(HOST, PORT))
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Crtl+C Pressed. Shutting down.")
