"""
### BEGIN NODE INFO
[info]
name = AMO8 Server
version = 1.0.0
description = Controls the AMO8 Box
instancename = AMO8 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from labrad.units import WithUnit

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

import time

TERMINATOR = '\r\n'

class AMO8Server(SerialDeviceServer):
    """
    Controls AMO8 Power Supply which controls ion pumps.
    """
    name = 'AMO8 Server'
    regKey = 'AMO8 Server'
    serNode = 'MongKok'
    port = 'COM57'

    timeout = WithUnit(3.0, 's')
    baudrate = 38400

    # GENERAL
    @setting(11, 'Clear', returns='s')
    def clear(self, c):
        """
        Clear all voltages & states.
        Returns:
            (str): response from device
        """
        yield self.ser.write('clear.w' + TERMINATOR)
        resp = yield self.ser.read_line()
        returnValue(resp)

    @setting(12, 'Inputs', returns='*s')
    def inputs(self, c):
        """
        Read high voltage inputs and current draws.
        Returns:
            [str, str, str, str]:
        """
        yield self.ser.write('HVin.r' + TERMINATOR)
        time.sleep(0.25)
        resp = yield self.ser.read()
        resp = yield self._parse(resp)
        returnValue(resp)

    # ON/OFF
    @setting(111, 'Toggle', channel='i', power='b', returns='s')
    def toggle(self, c, channel, power):
        """
        Set whether a channel is on or off.
        Args:
            channel (int)   : the channel to read/write
            power   (bool)  : whether channel is to be on or off
        Returns:
            (float): pump power status
        """
        msg = ''
        yield self.ser.write(msg + TERMINATOR)
        time.sleep(0.25)
        resp = yield self.ser.read()
        resp = yield self._parse(resp)
        returnValue(resp)

    @setting(112, 'Toggle Read', channel='i', returns='s')
    def toggleRead(self, c, channel=None):
        """
        Read whether a channel is on or off.
        Args:
            channel (int)   : the channel to read/write
        Returns:
                    (float): channel power status
        """
        if power:
            yield self.ser.write('G' + TERMINATOR)
        else:
            yield self.ser.write('B' + TERMINATOR)
        time.sleep(0.25)
        resp = yield self.ser.read()
        resp = resp.strip()
        returnValue(resp)

    # Voltage
    @setting(211, 'Voltage', channel='i', power='b', returns='s')
    def voltage(self, c, channel, voltage):
        """
        Set whether a channel is on or off.
        Args:
            channel (int)   : the channel to read/write
            voltage (bool)  : the channel voltage to set
        Returns:
            (float): pump power status
        """
        msg = ''
        yield self.ser.write(msg + TERMINATOR)
        time.sleep(0.25)
        resp = yield self.ser.read()
        resp = yield self._parse(resp)
        returnValue(resp)

    @setting(212, 'Voltage read', returns='v')
    def voltage_all(self, c):
        """
        Get ion pump pressure in mbar
        Returns:
            (float): ion pump pressure
        """
        yield self.ser.write('Tb' + TERMINATOR)
        time.sleep(0.25)
        resp = yield self.ser.read()
        returnValue(float(resp))


    #Helper functions
    def _parse(self, resp):
        #split ***
        resp = resp.split('\r\n')[:-1]
        #
        resp = [string.split(':')[-1].strip() for string in resp]
        return resp


if __name__ == '__main__':
    from labrad import util
    util.runServer(AMO8Server())