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
from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks
from labrad.server import setting

SERVERNAME = 'lakeshore336Server'
TIMEOUT = 1.0
BAUDRATE = 57600
CHANNELS = ['A', 'B', 'C', 'D', '0']

class Lakeshore336Server(SerialDeviceServer):
    name = 'Lakeshore336Server'
    regKey = 'Lakeshore336Server'
    port = None
    serNode = getNodeName()
    timeout = T.Value(TIMEOUT,'s')

    def initServer(self):
        # if not self.regKey or not self.serNode: raise SerialDeviceError('Must define regKey and serNode attributes')
        # port = yield self.getPortFromReg(self.regKey)
        # self.port = port
        port=24 #tmp
        try:
            serStr = yield self.findSerial(self.serNode)
            self.initSerial(serStr, port, baudrate=BAUDRATE)
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print
                'Could not find serial server for node: %s' % self.serNode
                print
                'Please start correct serial server'
            elif e.code == 1:
                print
                'Error opening serial connection'
                print
                'Check set up and restart serial server'
            else:
                raise

    # READ TEMPERATURE
    @setting(111, channel='s', returns='*1v')
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
        yield self.ser.write('KRDG? %d' % channel)
        resp = yield self.ser.read()
        resp = np.array(resp.split(','))
        returnValue(resp)


    @inlineCallbacks
    def read_temperature(self, channel = None):
        if channel not in CHANNELS:
            raise Exception('Channel must be one of: ' + str(CHANNELS))
        resp = yield self.query('KRDG? %d' % channel)
        resp = np.array(resp.split(','))
        returnValue(resp)