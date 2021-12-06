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

import time

from labrad.server import setting
from labrad.units import WithUnit

from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

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
        msg = 'clear.w' + TERMINATOR
        yield self.ser.write(msg)
        resp = yield self.ser.read_line()
        returnValue(resp)

    @setting(12, 'Inputs', returns='(vvvv)')
    def inputs(self, c):
        """
        Read high voltage inputs and current draws.
        Returns:
            ()
        """
        msg = 'HVin.r' + TERMINATOR
        yield self.ser.write(msg)
        v1 = yield self.ser.read_line()
        v2 = yield self.ser.read_line()
        i1 = yield self.ser.read_line()
        i2 = yield self.ser.read_line()
        resp = v1 +
        resp = self._parse()
        returnValue(resp)

    # ON/OFF
    @setting(111, 'Toggle', channel='i', power='i', returns='b')
    def toggle(self, c, channel, power):
        """
        Set a channel to be on or off.
        Args:
            channel (int)   : the channel to read/write
            power   (bool)  : whether channel is to be on or off
        Returns:
                    (bool)  : result
        """
        msg = 'out.w ' + str(channel) + str() + TERMINATOR
        yield self.ser.write(msg)
        #read and parse
        resp = yield self.ser.read_line()
        resp = self._parse(resp, False)
        #convert string to bool
        if resp == 'ON':
            resp = True
        elif resp == 'OFF':
            resp = False
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
        resp = None
        #read all channels if not specified
        if not channel:
            yield self.ser.write('out.r' + TERMINATOR)
            #wait for all data to be returned
            time.sleep(0.25)
            resp = yield self.ser.read()
            resp = yield self._parse(resp, True)
        else:
            yield self.ser.write('out.r ' + str(channel) + TERMINATOR)
            resp = yield self.ser.read_line()
            resp = yield self._parse(resp, False)
        returnValue(resp)

    # Voltage
    @setting(211, 'Voltage', channel='i', voltage='v', returns='s')
    def voltage(self, c, channel, voltage):
        """
        Set the voltage of a channel.
        Args:
            channel (int)   : the channel to read/write
            voltage (bool)  : the channel voltage to set
        Returns:
                    (float) : channel voltage
        """
        msg = 'vout.w ' + str(channel) + str(voltage) + TERMINATOR
        yield self.ser.write(msg)
        resp = yield self.ser.read_line()
        resp = yield self._parse(resp, False)
        returnValue(float(resp))

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
    def _parse(self, resp, multiple):
        #split response by delimiter
        resp = resp.split('\r\n')[:-1]
        #get only values
        resp = [string.split(':')[-1].strip() for string in resp]
        return resp


if __name__ == '__main__':
    from labrad import util
    util.runServer(AMO8Server())