"""
### BEGIN NODE INFO
[info]
name = TwisTorr 74 Turbopump Server
version = 1.0.0
description = Talks to the TwisTorr 74 Turbopump
instancename = TwisTorr74Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 5

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from __future__ import absolute_import
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGs_Control.lib.servers.serial.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
#from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.server import setting
from labrad.support import getNodeName
from labrad.types import Value

import time
import numpy as np

SERVERNAME = 'twistorr74server'
TIMEOUT = 5.0
BAUDRATE = 9600

class TwisTorr74Server(SerialDeviceServer):
    name = 'TwisTorr74Server'
    regKey = 'TwisTorr74Server'
    serNode = getNodeName()
    timeout = Value(TIMEOUT, 's')

    STX_msg = b'\x02'
    ADDR_msg = b'\x80'
    READ_msg = b'\x30'
    WRITE_msg = b'\x31'
    ETX_msg = b'\x03'

    ERRORS_msg = {
        b'\x15': "Execution failed",
        b'\x32': "Unknown window",
        b'\x33': "Data type error",
        b'\x34': "Value out of range",
        b'\x35': "Window disabled",
    }

    @inlineCallbacks
    def initServer( self ):
        # if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        # port = yield self.getPortFromReg( self.regKey )
        self.port = 'COM32'
        try:
            serStr = yield self.findSerial( self.serNode )
            print(serStr)
            self.initSerial( serStr, self.port, baudrate = BAUDRATE, timeout = self.timeout)
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
    @setting(111,'Read Pressure', returns='v')
    def pressure_read(self, c):
        """
        Get pump pressure
        Returns:
            (float): pump pressure in ***
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg = b'224', DIR_msg = self.READ_msg)
        yield self.ser.write(message)

        #read and parse answer
        time.sleep(1.0)
        resp = yield self.ser.read()
        try:
            resp = yield self._parse_answer(resp)
        except Exception as e:
            print(e)
            raise

        float(resp)
        returnValue(resp)

    def _create_message(self, CMD_msg, DIR_msg, DATA_msg = b''):
        msg = self.STX_msg + self.ADDR_msg + CMD_msg + DIR_msg + DATA_msg + self.ETX_msg
        msg = bytearray(msg)

        CRC_msg = 0x00
        for byte in msg[1:]:
            CRC_msg ^= byte

        CRC_msg = hex(CRC_msg)[2:]
        msg.extend(CRC_msg)
        msg = bytes(msg)
        return msg

    def _parse_answer(self, answer):
        if answer == (''):
            raise Exception ('No response from device')

        # remove STX, ADDR, and CRC
        ans = bytearray(answer)
        ans = ans[2:-3]

        #check if we have CMD and DIR and remove them if so
        if len(ans) > 1:
            ans = ans[4:]
            ans = ans.decode()
        #otherwise process return message for errors
        elif len(ans) == 1:
            ans = bytes(ans)
            print(ans)
            if ans in self.ERRORS_msg:
                raise Exception(self.ERRORS_msg[ans])

        return bytes(ans)

if __name__ == '__main__':
    from labrad import util
    util.runServer(TwisTorr74Server())