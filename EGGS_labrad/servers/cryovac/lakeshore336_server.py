"""
### BEGIN NODE INFO
[info]
name = Lakeshore336 Server
version = 1.0
description = Talks to the Lakeshore336 Temperature Controller
instancename = Lakeshore336 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

# imports
from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

import numpy as np
from time import sleep
from serial import PARITY_ODD

from EGGS_labrad.servers import PollingServer
from EGGS_labrad.servers import SerialDeviceServer

INPUT_CHANNELS = ['A', 'B', 'C', 'D', '0']
OUTPUT_CHANNELS = [1, 2, 3, 4]
TERMINATOR = '\r\n'

TEMPSIGNAL = 122485


class Lakeshore336Server(SerialDeviceServer, PollingServer):
    """
    Talks to the Lakeshore 336 Temperature Controller.
    """

    name = 'Lakeshore336 Server'
    regKey = 'Lakeshore336 Server'
    serNode = 'MongKok'
    port = 'COM24'

    timeout = WithUnit(5.0, 's')
    baudrate = 57600
    bytesize = 7
    parity = PARITY_ODD  # 0 is odd parity
    stopbits = 1

    # SIGNALS
    temp_update = Signal(TEMPSIGNAL, 'signal: temperature update', '(vvvv)')


    # TEMPERATURE DIODES
    @setting(111, 'Read Temperature', channel='s', returns='*1v')
    def temperature_read(self, c, channel=None):
        """
        Get sensor temperature.
        Arguments:
            channel (str): sensor channel to measure
        Returns:
            (*float): sensor temperature in Kelvin
        """
        if channel is None:
            channel = '0'
        elif channel not in INPUT_CHANNELS:
            raise Exception('Invalid input: channel must be one of: ' + str(INPUT_CHANNELS))
        # query
        yield self.ser.acquire()
        yield self.ser.write('KRDG? ' + str(channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # parse
        resp = np.array(resp.split(','), dtype=float)
        resp = tuple(resp)
        # update
        self.temp_update(resp)
        returnValue(resp)


    # HEATER
    @setting(211, 'Heater Setup', output_channel='i', resistance='i', max_current=['i', 'v'], returns='(iv)')
    def heater_setup(self, c, output_channel, resistance=None, max_current=None):
        """
        Set up the physical parameters of the heater.
        This should be done after the heater mode is set.
        Arguments:
            output_channel  (int): the heater channel
            resistance      (int): the heater resistance setting (1 = 25 Ohms, 2 = 50 Ohms)
            max_current     (float): maximum heater output current
        Returns:
                            (int, float): (resistance, max_current)
        """
        chString = 'HTRSET'
        # setter
        if (resistance is not None) and (max_current is not None):
            output_msg = chString + ' ' + str(output_channel) + ',' + str(resistance) + ',0,' + str(max_current) + ',1' + TERMINATOR
            yield self.ser.acquire()
            yield self.ser.write(output_msg)
            sleep(0.05)
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # return value
        resp = resp.split(',')
        resp = (int(resp[0]), float(resp[2]))
        returnValue(resp)

    @setting(212, 'Heater Mode', output_channel='i', mode='i', input_channel='i', returns='(ii)')
    def heater_mode(self, c, output_channel, mode=None, input_channel=None):
        """
        Set the output mode of the heater.
        Arguments:
            output_channel  (int): the heater channel
            mode            (int): heater operation mode (0=off, 1=PID, 2=zone, 3=open loop,
                                                        4=monitor out, 5=warmup)
            input_channel   (int): the temperature diode channel to control the output
        Returns:
                            (int, int): the output mode and linked input channel
        """
        chString = 'OUTMODE'
        # setter
        if (mode is not None) and (input_channel is not None):
            output_msg = chString + ' ' + str(output_channel) + ',' + str(mode) + ',' + str(input_channel) + ',0' + TERMINATOR
            yield self.ser.acquire()
            yield self.ser.write(output_msg)
            sleep(0.05)
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write(chString + '?' + str(output_channel) + ' ' + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # return value
        resp = np.array(resp.split(','), dtype=int)
        resp = tuple(resp[:2])
        returnValue(resp)

    @setting(221, 'Heater Range', output_channel='i', range='i', returns='i')
    def heater_range(self, c, output_channel, range=None):
        """
        Set or query heater range.
        Arguments:
            output_channel  (int): the heater channel
            range           (int): the heater range (0=off, 1=1% of max, 2=10% of max, 3=100% of max)
        Returns:
            (int): the heater range
        """
        chString = 'RANGE'
        # setter
        if range is not None:
            output_msg = chString + ' ' + str(output_channel) + ',' + str(range) + TERMINATOR
            yield self.ser.acquire()
            yield self.ser.write(output_msg)
            sleep(0.05)
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # return value
        returnValue(int(resp))

    @setting(213, 'Heater Power', output_channel='i', power=['i', 'v'], returns='v')
    def heater_power(self, c, output_channel, power=None):
        """
        Set or query heater power.
        If heater is in manual mode, then heater directly controls power/current.
        If heater is in closed loop mode, then heater sets power/current offset for PID.
        Arguments:
            output_channel (int): the heater channel
            power (float): the heater power as a percentage of max amount
        Returns:
            (float): the heater power
        """
        chString = 'MOUT'
        # setter
        if power is not None:
            output_msg = chString + ' ' + str(output_channel) + ',' + str(power) + TERMINATOR
            yield self.ser.acquire()
            yield self.ser.write(output_msg)
            sleep(0.05)
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # return value
        returnValue(float(resp))

    @setting(231, 'Heater PID', output_channel='i', prop='v', integ='v', diff='v', returns='(vvv)')
    def heater_PID(self, c, output_channel, prop=None, integ=None, diff=None):
        """
        Set or query heater PID parameters. Only available if heater is in PID mode.
        Arguments:
            output_channel (int): the heater channel
            prop           (float): Proportional
            integ           (float): Integral
            diff           (float): Derivative
        Returns:
                            (float, float, float): the PID parameters
        """
        chString = 'PID'
        if all(vals != None for vals in [prop, integ, diff]):
            output_msg = chString + ' ' + str(output_channel) + ',' + str(prop) + ',' + str(integ) + ',' + str(diff) + TERMINATOR
            yield self.ser.acquire()
            yield self.ser.write(output_msg)
            sleep(0.05)
            self.ser.release()
        # query
        yield self.ser.acquire()
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # return value
        resp = np.array(resp.split(','), dtype=float)
        returnValue(tuple(resp))

    @setting(232, 'Heater Setpoint', output_channel='i', setpoint='v', returns='v')
    def heater_setpoint(self, c, output_channel, setpoint=None):
        """
        Set the heater setpoint in closed-loop output mode.
        Arguments:
            output_channel  (int): the heater channel
            setpoint        (float): the setpoint (in Kelvin)
        Returns:
                            (float): the setpoint (in Kelvin)
        """
        chString = 'SETP'
        # setter
        if setpoint is not None:
            output_msg = chString + ' ' + str(output_channel) + ',' + str(setpoint) + TERMINATOR
            yield self.ser.acquire()
            yield self.ser.write(output_msg)
            sleep(0.05)
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()

        returnValue(float(resp))


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for temperature readout.
        """
        yield self.temperature_read(None, None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(Lakeshore336Server())