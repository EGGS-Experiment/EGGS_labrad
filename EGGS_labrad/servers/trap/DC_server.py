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

from time import sleep

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

    timeout = WithUnit(5.0, 's')
    baudrate = 38400


    # SIGNALS
    toggle_update = Signal(999997, 'signal: toggle update', '(ib)')
    voltage_update = Signal(999999, 'signal: voltage update', '(iv)')
    hv_update = Signal(999998, 'signal: hv update', '(vv)')


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
        sleep(0.2)
        v1 = yield self.ser.read_line('\n')
        i1 = yield self.ser.read_line('\n')
        self.ser.release()
        # parse input
        inputs = [float((tmpval.strip().split(':'))[1]) for tmpval in (v1, i1)]
        inputs = tuple(inputs)
        self.hv_update(inputs)
        returnValue(inputs)


    # ON/OFF
    @setting(111, 'Toggle', channel='i', power=['i','b'], returns='b')
    def toggle(self, c, channel, power=None):
        """
        Set a channel to be on or off.
        Args:
            channel (int)   : the channel to read/write. -1 does all channels
            power   (bool)  : whether channel is to be on or off
        Returns:
                    (bool)  : result
        """
        if (type(power) == int) and (power not in (0, 1)):
            raise Exception('Error: invalid input. Must be a boolean, 0, or 1.')
        yield self.ser.acquire()
        if power is not None:
            yield self.ser.write('out.w {:d} {:d}\r\n'.format(channel, power))
        else:
            yield self.ser.write('out.r {:d}\r\n'.format(channel))
        # get response
        resp = yield self.ser.read_line('\n')
        resp = resp.strip()
        # parse response
        if resp == 'ON':
            resp = True
        elif resp == 'OFF':
            resp = False
        else:
            raise Exception('Error: bad readback from device.')
        self.ser.release()
        # send signal to all other listeners
        self.toggle_update((channel, resp), self.getOtherListeners(c))
        returnValue(resp)

    @setting(121, 'Toggle All', power=['i', 'b'], returns=['', '*b'])
    def toggle_all(self, c, power=None):
        """
        Get/set power state of all channels.
        Args:
            power   (bool)  : whether channels are to be on or off.
        Returns:
                    (*bool) : power state of all channels.
        """
        if (type(power) == int) and (power not in (0, 1)):
            raise Exception('Error: invalid input. Must be a boolean, 0, or 1.')
        # set power states
        yield self.ser.acquire()
        if power is not None:
            if power is True:
                yield self.ser.write('allon.w\r\n')
            elif power is False:
                yield self.ser.write('alloff.w\r\n')
            yield self.ser.read_line('\n')
            self.ser.release()
            return
        else:
            yield self.ser.write('out.r\r\n')
        self.ser.release()
        # get power states
        resp = yield self._parse()
        resp = [True if val == 'ON' else False for val in resp]
        returnValue(resp)


    # VOLTAGE
    @setting(211, 'Voltage', channel='i', voltage='v', returns='v')
    def voltage(self, c, channel=None, voltage=None):
        """
        Set the voltage of a channel.
        Args:
            channel (int)   : the channel to read/write
            voltage (float)  : the channel voltage to set
        Returns:
                    (float) : channel voltage
        """
        # setter
        if voltage is not None:
            yield self.ser.acquire()
            yield self.ser.write('vout.w {:d} {:f}\r\n'.format(channel, voltage))
        # getter
        elif channel is not None:
            yield self.ser.acquire()
            yield self.ser.write('vout.r {:d}\r\n'.format(channel))
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        # parse response
        resp = (resp.strip())[:-1]
        # send signal to all other listeners
        self.voltage_update((channel, resp), self.getOtherListeners(c))
        returnValue(float(resp))


    @setting(221, 'Voltage All', returns='*v')
    def voltage_all(self, c):
        """
        Get the voltages of all channels.
        Returns:
                    (*float) : voltages of all channels.
        """
        yield self.ser.acquire()
        yield self.ser.write('vout.r\r\n')
        self.ser.release()
        resp = yield self._parse()
        resp = [float(val[:-1]) for val in resp]
        returnValue(resp)

    # RAMP
    @setting(311, 'Ramp', channel='i', voltage='v', rate='v', returns='*s')
    def ramp(self, c, channel, voltage, rate):
        """
        Ramps the voltage of a channel at a given rate.
        Args:
            channel (int)   : the channel to read/write
            voltage (float) : the ramp endpoint (in Volts).
            rate    (float) : the rate to ramp at (in Volts/s)
        Returns:
                    (str)   : success string of ramp
        """
        msg = 'ramp.w {:d} {:f} {:f}\r\n'.format(channel, voltage, rate)
        yield self.ser.acquire()
        yield self.ser.write(msg)
        sleep(0.2)
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = resp.strip().split(', ')
        returnValue(resp)

    @setting(312, 'Ramp Multiple', channels='*i', voltages='*v', rates='*v', returns='*s')
    def rampMultiple(self, c, channels, voltages, rates):
        """
        Simultaneously ramps the voltage of multiple channels.
        Arguments:
            channel (*int)  : the channels to read/write
            voltage (*float): the ramp endpoints (in Volts)
            rate    (*float): the rates to ramp at (in Volts/s)
        Returns:
                    (str)   : success strings of the ramps
        """
        # check parameters are specified for all channels
        if (len(channels) != len(voltages)) and (len(voltages) != len(rates)):
            raise Exception('Error: all parameters must be specified for all channels.')
        # reformat the input parameters
        param_list = zip(channels, voltages, rates)
        # send commands to device
        resp = []
        yield self.ser.acquire()
        for channel, voltage, rate in param_list:
            msg = 'ramp.w {:d} {:f} {:f}\r\n'.format(channel, voltage, rate)
            yield self.ser.write(msg)
            resp_tmp = yield self.ser.read_line('\n')
            resp.append(resp_tmp)
        self.ser.release()
        # todo: fix for better responses
        #resp_processing_func = lambda resp_tmp: resp_tmp.strip().split(': ')
        #resp = list((resp_processing_func, resp))
        #resp = [resp[0] for strings in resp]
        returnValue(resp)


    # HELPER
    @inlineCallbacks
    def _poll(self):
        yield self.inputs(None)

    @inlineCallbacks
    def _parse(self):
        yield self.ser.acquire()
        # wait until device has finished writing
        sleep(1)
        # todo: check this is OK and see if we can somehow do a definite read
        resp = yield self.ser.read()
        self.ser.release()
        # separate response for each channel
        resp = resp.strip().split('\r\n')
        # remove channel number
        resp = [val.split(': ')[1] for val in resp]
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(DCServer())
