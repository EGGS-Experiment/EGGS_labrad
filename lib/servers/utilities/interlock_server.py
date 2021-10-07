"""
### BEGIN NODE INFO
[info]
name = Interlock Server
version = 1.0.0
description = Runs interlocks for different devices
instancename = Interlock Server

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
from labrad.server import setting, LabradServer
from labrad.support import getNodeName
import time

import numpy as np

SERVERNAME = 'Interlock Server'

class Lakeshore336Server(SerialDeviceServer):
    name = 'Interlock Server'
    regKey = 'InterlockServer'
    serNode = getNodeName()
    OUTPUT_MODES = [0, 1, 2, 3, 4, 5]

    # def initServer(self):
    #     #temp workaround since serial server is a pos
    #     self.ser = Serial(port = 'COM24', baudrate = BAUDRATE, bytesize = BYTESIZE, parity = PARITY, stopbits = STOPBITS)
    #     self.ser.timeout = TIMEOUT

    @inlineCallbacks
    def initServer(self):
        if not self.regKey or not self.serNode:
            raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        # port = yield self.getPortFromReg( self.regKey )
        try:
            serStr = yield self.findSerial( self.serNode )
            print(serStr)
            self.initSerial( serStr, port, baudrate = BAUDRATE, bytesize = BYTESIZE, parity = PARITY, stopbits = STOPBITS)
        #todo: make sure in kelvin

    # HEATER
    @setting(211, 'Configure Heater', output_channel = 'i', mode = 'i', input_channel = 'i', returns = '*1v')
    def heater_mode(self, c, output_channel, mode = None, input_channel = None):
        """
        Configure or query the desired heater
        Args:
            output_channel  (int): the heater channel
            mode            (int): heater operation mode (0 = off, 1 = PID, 2 = zone, 3  = open loop,
                                                        4 = monitor out, 5 = warmup)
            input_channel   (int): the temperature diode channel to control the output
        Returns:
                            ([int, int]): the output mode and linked input
        """
        chString = 'OUTMODE'

        #check for errors

        #send message if not querying
        if mode is not None and input_channel in INPUT_CHANNELS:
            output_msg = chString + ' ' + str(output_channel) + ',' + str(mode) + ',' + str(input_channel) + ',0' + TERMINATOR
            yield self.ser.write(output_msg)

        #issue query
        yield self.ser.write(chString + '?' + TERMINATOR)
        resp = yield self.ser.read()
        resp = np.array(resp.split(','), dtype=int)
        resp = resp[:2]
        returnValue(resp)

    @setting(212, 'Setup Heater', output_channel = 'i', resistance = 'i', max_current = 'v', returns = '*1v')
    def heater_setup(self, c, output_channel, resistance = None, max_current = None):
        """
        Set up or query the desired heater
        Args:
            output_channel  (int): the heater channel
            resistance      (int): the heater resistance setting (1 = 25 Ohms, 2 = 50 Ohms)
            max_current     (int): maximum heater output current
        Returns:
                            ([]): fd
        """
        chString = 'HTRSET'

        #check for errors

        #send message if not querying
        if resistance is not None and max_current is not None:
            output_msg = ' ' + str(output_channel) + ',' + str(resistance) + ',0,' + str(max_current) + ',2' + TERMINATOR
            yield self.ser.write(chString + output_msg)

        #issue query
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read()
        resp = resp.split(',')
        resp = [int(resp[0]), int(resp[1]), float(resp[2])]
        returnValue(resp)

    @setting(221, 'Set Heater Range', output_channel = 'i', range = 'i', returns = 'i')
    def heater_range(self, c, output_channel, range = None):
        """
        Set or query heater range. Only available if heater is in Zone mode.
        Args:
            output_channel (int): the heater channel
            range (int): the heater range (0 = off, 1 = Low, 2 = Medium, 3 = High)
        Returns:
            (int): the heater range
        """
        chString = 'RANGE'

        #check for errors

        if range is not None:
            output_msg = ' ' + str(output_channel) + ',' + str(range) + TERMINATOR
            yield self.ser.write(chString + output_msg)

        #issue query
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield int(self.ser.read())
        returnValue(resp)

if __name__ == '__main__':
    from labrad import util
    util.runServer(Lakeshore336Server())