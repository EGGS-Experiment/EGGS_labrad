"""
### BEGIN NODE INFO
[info]
name = Temperature Controller Server
version = 1.0.0
description = Talks to the Lakeshore 336 Temperature Controller
instancename = Lakeshore336Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from __future__ import absolute_import
from twisted.internet.defer import inlineCallbacks, returnValue
from common.lib.servers.serialdeviceserver import SerialDeviceServer
#from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.server import setting
from labrad.support import getNodeName

from serial import Serial
import serial #workaround temporary

import numpy as np
import time #tmp

SERVERNAME = 'lakeshore336Server'
TIMEOUT = 1.0
BAUDRATE = 57600
BYTESIZE = 7
PARITY = serial.PARITY_ODD #0 is odd parity
STOPBITS = 1
CHANNELS = ['A', 'B', 'C', 'D', '0']

class Lakeshore336Server(SerialDeviceServer):
    name = 'Lakeshore336Server'
    regKey = 'Lakeshore336Server'
    #port = None
    serNode = getNodeName()

    #@inlineCallbacks
    def initServer(self):
        #temp workaround since serial server is a pos
        self.ser = Serial(port = 'COM24', baudrate = BAUDRATE, bytesize = BYTESIZE, parity = PARITY, stopbits = STOPBITS)
        self.ser.timeout = TIMEOUT

    # READ TEMPERATURE
    @setting(111,'read_temperature', channel = 's', returns='*1v')
    def read_temperature(self, c, channel):
        """
        Get sensor temperature
        Args:
            channel (str): sensor channel to measure
        Returns:
            (*float): sensor temperature in Kelvin
        """
        if channel not in CHANNELS:
            raise Exception('Channel must be one of: ' + str(CHANNELS))
        yield self.ser.write('KRDG? ' + str(channel) + '\r\n')
        resp = yield self.ser.read_until()
        resp = resp[:-2]
        resp = np.array(resp.split(','), dtype=float)
        returnValue(resp)

if __name__ == '__main__':
    from labrad import util
    util.runServer(Lakeshore336Server())