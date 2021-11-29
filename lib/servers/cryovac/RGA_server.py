"""
### BEGIN NODE INFO
[info]
name = RGA Server
version = 1.3
description = Connects to the SRS200 RGA

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

'''
Created May 22, 2016
@author: Calvin He
'''

from labrad.units import WithUnit
from labrad.server import Signal, setting
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer, SerialDeviceError, SerialConnectionError, PortRegError

from twisted.internet.task import LoopingCall
from twisted.internet.defer import returnValue, inlineCallbacks

class RGA_Server(SerialDeviceServer):
    name = 'RGA Server'
    regKey = 'RGAServer'
    port = 'COM48'
    serNode = 'mongkok'

    timeout = WithUnit(3.0, 's')
    baudrate = 28800

    def initServer(self):
        self.listeners = set()

    @setting(1, returns='s')
    def identify(self, c):
        '''
        Returns the RGA's IDN.
        '''
        yield self.ser.write('ID?\r\n')
        resp = yield self.ser.read()
        returnValue(resp)

    @setting(2, value='w',returns='s')
    def filament(self, c, value=None):
        '''
        Sets the filament on/off mode, or read its value.
        ".filament(0)" shuts off the filament.  RGACOM command: "fl0"
        ".filament(1)" turns on the filament.  RGACOM command: "fl1"
        ".filament()" asks for the filament mode.  RGACOM command: "fl?"
        '''
        notified = self.getOtherListeners(c)
        if value > 1:
            message = 'Input out of range. Acceptable inputs: 0 and 1.'
        elif value == 1:
            yield self.ser.write_line('fl1')
            message = 'Filament on command sent.'
            self.filsignal(1, notified)
        elif value == 0:
            yield self.ser.write_line('fl0')
            message = 'Filament off command sent.'
            self.filsignal(0, notified)
        elif not value:
            yield self.ser.write_line('fl?')
            message = 'fl? command sent.'
            self.quesignal(message, self.listeners.copy())
        returnValue(message)

    @setting(3, value='v', returns='s')
    def mass_lock(self, c, value):
        '''
        Sets the mass lock for the RGA.  Acceptable range: [1,200].  RGACOM command:  "mlx"
        ".mass_lock(x)" sets the mass filter to x (positive integer representing amu).
        '''
        notified = self.getOtherListeners(c)
        if value<1 or value>200:
            message = 'Mass out of range.  Acceptable range: [1,200]'
        else:
            yield self.ser.write_line('ml'+str(value))
            message = 'Mass lock for '+str(value)+' amu command sent.'
            self.mlsignal(value, notified)
        returnValue(message)

    @setting(4, value='w', returns='s')
    def high_voltage(self, c, value=None):
        '''
        Sets the electron multiplier voltage.  Acceptable range: [0,2500]
        ".high_voltage()" asks for the electron multiplier voltage.  RGACOM command: "hv?"
        ".high_voltage(x)" sets the electron multiplier voltage to x (positive integer representing volts).  RGA COM command: "hvx"
        '''
        notified = self.getOtherListeners(c)
        if value==None:
            yield self.ser.write_line('hv?')
            message = 'hv? request sent.'
            self.quesignal(message, self.listeners.copy())
        elif value > 2500:
            message = 'Voltage out of range.  Acceptable range: [0,2500]'
        else:
            yield self.ser.write_line('hv'+str(value))
            message = 'High voltage (electron multiplier) command sent.'
            self.hvsignal(value, notified)
        returnValue(message)

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        if c.ID in notified:
            notified.remove(c.ID)
        return notified

if __name__ == "__main__":
    from labrad import util
    util.runServer(RGA_Server())
