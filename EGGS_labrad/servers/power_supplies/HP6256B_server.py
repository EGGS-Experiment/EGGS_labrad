"""
### BEGIN NODE INFO
[info]
name = HP6256B Server
version = 1.0.0
description = Uses the ARTIQ DAC to communicate with the HP6256B power supply for loading via getter.
instancename = HP6256BServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import setting, inlineCallbacks

from twisted.internet.defer import returnValue
from EGGS_labrad.servers import ARTIQServer

TERMINATOR = '\r\n'


class HP6256B_server(ARTIQServer):
    """
    Uses the ARTIQ DAC to communicate with the HP6256B power supply for loading via getter.
    """

    name = 'HP6256B Server'
    regKey = 'HP6256BServer'


    # GENERAL
    @setting(11, 'Clear', returns='s')
    def clear(self, c):
        """
        Clear all voltages & states.
        Returns:
            (str): response from device
        """
        yield self.ser.acquire()
        yield self.ser.write('clear.w\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        returnValue(resp)


    # ON/OFF
    @setting(111, 'Toggle', channel='i', power='i', returns=['b', '*b'])
    def toggle(self, c, channel, power=None):
        """
        Set a channel to be on or off.
        Args:
            channel (int)   : the channel to read/write. -1 does all channels
            power   (bool)  : whether channel is to be on or off
        Returns:
                    (bool)  : result
        """
        if channel == -1:
            yield self.ser.acquire()
            if power is None:
                yield self.ser.write('out.r\r\n')
            elif power:
                yield self.ser.write('allon.w\r\n')
            else:
                yield self.ser.write('allon.w\r\n')
            self.ser.release()
            resp = yield self._parse()
            returnValue(list(map(bool, resp)))
        if power is not None:
            yield self.ser.acquire()
            yield self.ser.write('out.w {:d} {:d}\r\n'.format(channel, power))
        else:
            yield self.ser.write('out.r {:d}\r\n'.format(channel))
        # get response
        resp = yield self.ser.read_line('\r\n')
        self.ser.release()
        self.toggle_update((channel, resp))
        returnValue(bool(resp))


    # VOLTAGE
    @setting(211, 'Voltage', channel='i', voltage='v', returns=['v', '*v'])
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
            yield self.ser.write('vout.w {:d} {:f}\r\n'.format(channel, voltage))
            resp = yield self.ser.read_line('\r\n')
            self.ser.release()
            returnValue(float(resp))
        elif channel is not None:
            if channel == -1:
                yield self.ser.acquire()
                yield self.ser.write('vout.r\r\n')
                self.ser.release()
                resp = yield self._parse()
                returnValue(resp)
            else:
                yield self.ser.acquire()
                yield self.ser.write('vout.r {:d}\r\n'.format(channel))
                resp = yield self.ser.read_line('\r\n')
                self.ser.release()
                returnValue(float(resp))


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
        msg = 'ramp.w {:d} {:f} {:f}\r\n'.format(voltage, rate)
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line('\r\n')
        self.ser.release()
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(HP6256B_server())