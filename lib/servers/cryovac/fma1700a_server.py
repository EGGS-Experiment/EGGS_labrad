"""
### BEGIN NODE INFO
[info]
name = FMA1700A Server
version = 1.0.0
description = Controls the FMA1700A Mass Flow Meter via an Arduino
instancename = FMA1700A Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import time

from labrad.units import WithUnit
from labrad.server import setting, Signal

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

TERMINATOR = '\r\n'


class FMA1700AServer(SerialDeviceServer):
    """
    Controls FMA1700A Flow Meter for the ColdEdge system..
    """

    name = 'FMA1700A Server'
    regKey = 'FMA1700AServer'
    serNode = None
    port = None

    timeout = WithUnit(3.0, 's')
    baudrate = 38400

    # SIGNALS
    pressure_update = Signal(999999, 'signal: flow update', 'v')

    # STARTUP
    @setting(211, 'Read Pressure', returns='v')
    def pressure_read(self, c):
        """
        Get pump pressure
        Returns:
            (float): pump pressure in mbar
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg=b'224', DIR_msg=_TT74_READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read(19)
        resp = yield self._parse(resp)
        resp = float(resp)
        #send signal and return value
        self.pressure_update(resp)
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for pressure readout.
        """
        yield self.ser.write(b'\x02\x802240\x0387')
        resp = yield self.ser.read(19)
        resp = yield self._parse(resp)
        resp = float(resp)
        self.pressure_update(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(FMA1700AServer())