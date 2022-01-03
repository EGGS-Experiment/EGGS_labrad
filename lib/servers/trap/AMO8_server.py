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

from twisted.internet.defer import returnValue
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
    def toggle(self, c, channel=None, power=None):
        """
        Set a channel to be on or off.
        Args:
            channel (int)   : the channel to read/write
            power   (bool)  : whether channel is to be on or off
        Returns:
                    (bool)  : result
        """
        if power is not None:
            yield self.ser.acquire()
            yield self.ser.write('out.w {:d} {:d}\n'.format(channel, power))
            resp = yield self.ser.read_line('\n')
            self.ser.release()
            if resp == 'ON':
                return True
            elif resp == 'OFF':
                return False
        elif channel is not None:
            yield self.ser.acquire()
            yield self.ser.write('out.r {:d}\n'.format(channel))
            resp = yield self.ser.read_line('\n')
            self.ser.release()
            if resp == 'ON':
                return True
            elif resp == 'OFF':
                return False
        else:
            yield self.ser.acquire()
            yield self.ser.write('out.r\n')
            resp = list()
            for i in range(56):
                resp_tmp = yield self.ser.read_line('\n')
                resp_tmp = resp_tmp.split(':')[-1]
                if resp_tmp == 'ON':
                    resp[i] = True
                elif resp_tmp == 'OFF':
                    resp[i] = False
            self.ser.release()
            returnValue(resp)


    # VOLTAGE
    @setting(211, 'Voltage', channel='i', voltage='v', returns=['v','*v'])
    def voltage(self, c, channel=None, voltage=None):
        """
        Set the voltage of a channel.
        Args:
            channel (int)   : the channel to read/write
            voltage (float)  : the channel voltage to set
        Returns:
                    (float) : channel voltage
        """
        if voltage is not None:
            yield self.ser.acquire()
            yield self.ser.write('vout.w {:d} {:f}\n'.format(channel, voltage))
            resp = yield self.ser.read_line('\n')
            self.ser.release()
            resp = resp[:-1]
            returnValue(float(resp))
        elif channel is not None:
            yield self.ser.acquire()
            yield self.ser.write('vout.r {:d}\n'.format(channel))
            resp = yield self.ser.read_line('\n')
            self.ser.release()
            resp = resp[:-1]
            returnValue(float(resp))
        else:
            yield self.ser.acquire()
            yield self.ser.write('vout.r\n')
            resp = list()
            for i in range(56):
                resp[i] = yield self.ser.read_line('\n')
            resp = [float(txt.split(':')[-1][:-1]) for txt in resp]
            returnValue(resp)


    # RAMP
    @setting(311, 'Ramp', channel='i', voltage='v', rate='v', returns='s')
    def ramp(self, c, channel, voltage, rate):
        """
        Ramps the voltage of a channel at a given rate.
        Args:
            channel (int)   : the channel to read/write
            voltage (float) : the ramp endpoint
            rate    (float) : the rate to ramp at (in volts/ms)
        Returns:
                    (str)   : success state of ramp
        """
        msg = 'ramp.w {:d} {:f} {:f}'.format(voltage, rate)
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(AMO8Server())