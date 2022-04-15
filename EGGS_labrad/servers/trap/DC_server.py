"""
### BEGIN NODE INFO
[info]
name = DC Server
version = 1.0.0
description = Communicates with the AMO8 box for control of all DC voltages.
instancename = DCServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.units import WithUnit
from labrad.server import setting, Signal, inlineCallbacks

from twisted.internet.defer import returnValue
from EGGS_labrad.servers import SerialDeviceServer, PollingServer

TERMINATOR = '\r\n'


class DCServer(SerialDeviceServer, PollingServer):
    """
    Communicates with the AMO8 box for control of all DC voltages.
    """

    name = 'DC Server'
    regKey = 'DCServer'
    serNode = 'MongKok'
    port = 'COM3'

    timeout = WithUnit(3.0, 's')
    baudrate = 38400


    # SIGNALS
    voltage_update = Signal(999999, 'signal: voltage update', '(iv)')
    hv_update = Signal(999998, 'signal: hv update', '(vv)')
    toggle_update = Signal(999997, 'signal: toggle update', '(ib)')


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

    @setting(12, 'Inputs', returns='(vv)')
    def inputs(self, c):
        """
        Read high voltage inputs and current draws.
        Returns:
            (vv): (HVin1, Iin1)
        """
        yield self.ser.acquire()
        yield self.ser.write('HVin.r\r\n')
        v1 = yield self.ser.read_line('\n')
        i1 = yield self.ser.read_line('\n')
        self.ser.release()
        # parse input
        inputs = [float((tmpval.strip().split(':'))[1]) for tmpval in (v1, i1)]
        inputs = tuple(inputs)
        self.hv_update(inputs)
        returnValue(inputs)


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
        yield self.ser.acquire()
        if power is not None:
            yield self.ser.write('out.w {:d} {:d}\r\n'.format(channel, power))
        else:
            yield self.ser.write('out.r {:d}\r\n'.format(channel))
        # get response
        resp = yield self.ser.read_line('\r\n')
        resp = resp.strip()
        if resp == 'ON':
            resp = 1
        elif resp == 'OFF':
            resp = 0
        else:
            raise Exception('Error: bad readback from device.')
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
            yield self.ser.acquire()
            yield self.ser.write('vout.r {:d}\r\n'.format(channel))
            resp = yield self.ser.read_line('\r\n')
            self.ser.release()
            resp = (resp.strip())[:-1]
            print(resp)
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


    # HELPER
    @inlineCallbacks
    def _poll(self):
        yield self.inputs(None)

    @inlineCallbacks
    def _parse(self, data):
        resp = list()
        yield self.ser.acquire()
        for i in range(28):
            resp[i] = yield self.ser.read_line('\n')
        self.ser.release()
        resp = [float(txt.split(':')[-1][:-1]) for txt in resp]
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(DCServer())
