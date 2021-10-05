"""
### BEGIN NODE INFO
[info]
name = NIOPS-03 Power Supply Controller
version = 1.0.0
description = Controls NIOPS-03 Power Supply which controls ion pumps
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
from EGGs_Control.lib.servers.serial.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.server import setting
from labrad.support import getNodeName
from serial import PARITY_ODD

import numpy as np

SERVERNAME = 'NIOPS03Server'
TIMEOUT = 1.0
BAUDRATE = 115200
TERMINATOR = '\r\n'

class NIOPS03Server(SerialDeviceServer):
    name = 'NIOPS03Server'
    regKey = 'NIOPS03Server'
    serNode = getNodeName()

    QUERY_msg = b'\x05'

    @inlineCallbacks
    def initServer( self ):
        # if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        # port = yield self.getPortFromReg( self.regKey )
        port = 'COM3'
        self.port = port
        self.timeout = TIMEOUT
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

    # ON/OFF
    @setting(111,'Toggle IP', power = 'b')
    def toggle_ip(self, c, power = None):
        """
        Set or query whether ion pump is off or on
        Args:
            (bool): whether pump is to be on or off
        Returns:
            (float): pump power status
        """
        #create and send message to device
        if power == True:
            self.ser.write('G' + TERMINATOR)
        elif power == False:
            self.ser.write('B' + TERMINATOR)

        resp = yield self.ser.read()
        return

    @setting(112,'Toggle NP', power = 'b')
    def toggle_ip(self, c, power = None):
        """
        Set or query whether getter is off or on
        Args:
            (bool): whether getter is to be on or off
        Returns:
            (float): getter power status
        """
        #create and send message to device
        if power == True:
            self.ser.write('GN' + TERMINATOR)
        elif power == False:
            self.ser.write('BN' + TERMINATOR)

        resp = yield self.ser.read()
        return

if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())