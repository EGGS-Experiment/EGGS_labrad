"""
### BEGIN NODE INFO
[info]
name = TwisTorr 74 Turbopump Server
version = 1.0.0
description = Talks to the TwisTorr 74 Turbopump
instancename = TwisTorr74Server

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
from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.server import setting
from labrad.support import getNodeName
from serial import PARITY_ODD

import numpy as np

SERVERNAME = 'twistorr74server'
TIMEOUT = 1.0
BAUDRATE = 9600

class TwisTorr74Server(SerialDeviceServer):
    name = 'TwisTorr74Server'
    regKey = 'TwisTorr74Server'
    serNode = getNodeName()

    STX_msg = 0x02
    ADDR_msg = 0x80
    READ_msg = 0x30
    WRITE_msg = 0x31
    ETX_msg = 0x03

    # def initServer(self):
    #     #temp workaround since serial server is a pos
    #     self.ser = Serial(port = 'COM24', baudrate = BAUDRATE, bytesize = BYTESIZE, parity = PARITY, stopbits = STOPBITS)
    #     self.ser.timeout = TIMEOUT

    @inlineCallbacks
    def initServer( self ):
        # if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        # port = yield self.getPortFromReg( self.regKey )
        port = 'COM24'
        self.port = port
        #self.timeout = TIMEOUT
        try:
            serStr = yield self.findSerial( self.serNode )
            print(serStr)
            self.initSerial( serStr, port, baudrate = BAUDRATE)
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise

    # READ PRESSURE
    @setting(111,'read_temperature', returns='v')
    def read_temperature(self, c, channel):
        """
        Get pump pressure
        Returns:
            (float): pump pressure in ***
        """
        message = _create_message()
        yield self.ser.write(message)
        resp = yield self.ser.read()
        resp = _parse_answer(resp)
        #convert resp to float
        returnValue(resp)

    def _create_message(self, CMD_msg, DIR_msg, DATA_msg = 0x00):
        #0x02, 0x80, 0xe0 (cmd), 0x30 (read), 0x03, CRC (xor from 0x80 to incl 0x03)

        #checksum calculated by XORing all bits after STX
        CRC_msg = ADDR_msg ^ CMD_msg ^ DIR_msg ^ DATA_msg ^ ETX_msg
        #only add data to message if we are writing to controller
        if DIR_msg == WRITE_msg:
            msg = [STX_msg, ADDR_msg, CMD_msg, DIR_msg, DATA_msg, ETX_msg, CRC_msg]
        else if DIR_msg == READ_msg:
            msg = [STX_msg, ADDR_msg, CMD_msg, DIR_msg, ETX_msg, CRC_msg]
        return msg

    def _parse_answer(self, answer):
        #0x02, 0x80, 0xe0 (cmd), 0x30 (read), data (x.x e xx, 10b alphanumeric), 0x03, crc
        #remove STX, ADDR, and CRC
        ans = answer[2:-3]
        #check if we have CMD and DIR and remove them if so
        if len(ans) > 1:
            ans = ans[4:]
        return ans

if __name__ == '__main__':
    from labrad import util
    util.runServer(TwisTorr74Server())