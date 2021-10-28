"""
### BEGIN NODE INFO
[info]
name = Interlock Server
version = 1.0
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

from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.server import setting, LabradServer, Signal
from labrad.support import getNodeName
from twisted.internet.task import LoopingCall

import numpy as np

SERVERNAME = 'Interlock Server'

class InterlockServer(LabradServer):
    name = 'Interlock Server'
    regKey = 'InterlockServer'
    serNode = getNodeName()

    @inlineCallbacks
    def initServer(self):
        #connect to labrad
        self.cxn = labrad.connect()

        #connect servers
        self.reg = self.cxn.registry
        self.niops = self.cxn.niops03_server
        self.pump = self.cxn.twistorr74server

        #get polling interval
        yield self.reg.cd(['', 'Servers', 'Interlock Server'])
        self.poll_time = self.reg.get('poll_time')

        #setup poll loop
        self.poll_loop = LoopingCall(self.poll)

    #Polling functions
    @setting(111, 'Toggle Interlock', onoff = 'b', returns = '')
    def toggle_interlock(self, c, onoff):
        """
        Switch the interlock on or off
        Args:
            onoff       (bool): desired interlock state
        """
        if onoff == True:
            self.poll_loop.start(self.poll_time)
        elif onoff == False:
            self.poll_loop.stop()

    def poll(self):
        pressure = yield self.pump.read_pressure()
        if pressure > 1e-6:
            self.niops.toggle_ip(False)
            print("Interlock activated: switched off ion pump since pressure exceeded 1e-6 mbar")


if __name__ == '__main__':
    from labrad import util
    util.runServer(InterlockServer())