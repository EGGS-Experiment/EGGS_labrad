"""
### BEGIN NODE INFO
[info]
name = Lakeshore 336 Server
version = 1.0
description = Talks to the Lakeshore 336 Temperature Controller
instancename = Lakeshore 336 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.server import setting, Signal
from labrad.support import getNodeName
from labrad.units import WithUnit
from serial import PARITY_ODD
import time

import numpy as np

INPUT_CHANNELS = ['A', 'B', 'C', 'D', '0']
OUTPUT_CHANNELS = [1, 2, 3, 4]
TERMINATOR = '\r\n'

TEMPSIGNAL = 122485

class Lakeshore336Server(SerialDeviceServer):
    name = 'Lakeshore 336 Server'
    regKey = 'Lakeshore336Server'
    serNode = 'wanchai'
    port = 'COM6'

    timeout = WithUnit(1.0, 's')
    baudrate = 57600
    bytesize = 7
    parity = PARITY_ODD  # 0 is odd parity
    stopbits = 1

    tempupdate = Signal(TEMPSIGNAL, 'signal: temperature update', '*v')

    @inlineCallbacks
    def _check_errors(self, input, valid_inputs):
        """
        Checks user input for errors
        """
        if input not in valid_inputs:
            raise Exception("Value must be one of: " + str(valid_inputs))

    # TEMPERATURE DIODES
    @setting(111,'Read Temperature', output_channel = 's', returns='*1v')
    def temperature_read(self, c, output_channel):
        """
        Get sensor temperature
        Args:
            channel (str): sensor channel to measure
        Returns:
            (*float): sensor temperature in Kelvin
        """
        if output_channel not in INPUT_CHANNELS:
            raise Exception('Channel must be one of: ' + str(INPUT_CHANNELS))
        yield self.ser.write('KRDG? ' + str(output_channel) + TERMINATOR)
        time.sleep(0.1)
        resp = yield self.ser.read()
        resp = np.array(resp.split(','), dtype=float)
        returnValue(resp)

    # HEATER
    @setting(211, 'Configure Heater', output_channel = 'i', mode = 'i', input_channel = 'i', returns = '*1v')
    def heater_mode(self, c, output_channel, mode = None, input_channel = None):
        """
        Configure or query the desired heater
        Args:
            output_channel  (int): the heater channel
            mode            (int): heater operation mode (0 = off, 1 = PID, 2 = zone, 3  = open loop,
                                                        4 = monitor out, 5 = warmup)
            input_channel   (int): the temperature diode channel to control the output
        Returns:
                            ([int, int]): the output mode and linked input
        """
        chString = 'OUTMODE'

        #check for errors

        #send message if not querying
        if mode is not None and input_channel in INPUT_CHANNELS:
            output_msg = chString + ' ' + str(output_channel) + ',' + str(mode) + ',' + str(input_channel) + ',0' + TERMINATOR
            yield self.ser.write(output_msg)

        #issue query
        yield self.ser.write(chString + '?' + TERMINATOR)
        resp = yield self.ser.read()
        resp = np.array(resp.split(','), dtype=int)
        resp = resp[:2]
        returnValue(resp)

    @setting(212, 'Setup Heater', output_channel = 'i', resistance = 'i', max_current = 'v', returns = '*1v')
    def heater_setup(self, c, output_channel, resistance = None, max_current = None):
        """
        Set up or query the desired heater
        Args:
            output_channel  (int): the heater channel
            resistance      (int): the heater resistance setting (1 = 25 Ohms, 2 = 50 Ohms)
            max_current     (float): maximum heater output current
        Returns:
                            (int, float): Tuple of (resistance, max_current)
        """
        chString = 'HTRSET'

        #check for errors

        #send message if not querying
        if resistance is not None and max_current is not None:
            output_msg = ' ' + str(output_channel) + ',' + str(resistance) + ',0,' + str(max_current) + ',2' + TERMINATOR
            yield self.ser.write(chString + output_msg)

        #issue query
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read()
        resp = resp.split(',')
        resp = [int(resp[1]), float(resp[2])]
        returnValue(resp)

    @setting(213, 'Set Heater Range', output_channel = 'i', range = 'i', returns = 'i')
    def heater_range(self, c, output_channel, range = None):
        """
        Set or query heater range.
        Args:
            output_channel (int): the heater channel
            range (int): the heater range (0 = off, 1 = 1% of max, 2 = 10% of max, 3 = 100% of max)
        Returns:
            (int): the heater range
        """
        chString = 'RANGE'

        #check for errors

        if range is not None:
            output_msg = ' ' + str(output_channel) + ',' + str(range) + TERMINATOR
            yield self.ser.write(chString + output_msg)

        #issue query
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield int(self.ser.read())
        returnValue(resp)

    @setting(214, 'Set Heater Setpoint', output_channel = 'i', setpoint = 'v', returns = 'v')
    def heater_setpoint(self, c, output_channel, setpoint = None):
        """
        Set or query heater setpoint.
        Args:
            output_channel  (int): the heater channel
            setpoint        (float): the setpoint
        Returns:
                            (float): the setpoint
        """
        chString = 'SETP'
        if power is not None:
            output_msg = chString + ' ' + str(output_channel) + ',' + str(setpoint)+ TERMINATOR
            yield self.write(output_msg)

        #issue query
        resp = yield self.query(chString + '? ' + str(output_channel) + TERMINATOR)
        returnValue(float(resp))

    @setting(221, 'Autotune Heater', output_channel = 'i', input_channel = 'i', mode = 'i', returns = '*1v')
    def heater_setup(self, c, output_channel, input_channel = None, mode = None):
        """
        Set up or query the desired heater
        Args:
            output_channel  (int): the heater channel
            input_channel   (int): the input channel for control
            mode            (int): autotune mode (0 = P only, 1 = P & I only, 2 = PID)
        Returns:
                            (int, float): Tuple of (resistance, max_current)
        """
        chString = 'HTRSET'

        #check for errors

        #send message if not querying
        if resistance is not None and max_current is not None:
            output_msg = ' ' + str(output_channel) + ',' + str(resistance) + ',0,' + str(max_current) + ',2' + TERMINATOR
            yield self.ser.write(chString + output_msg)

        #issue query
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read()
        resp = resp.split(',')
        resp = [int(resp[1]), float(resp[2])]
        returnValue(resp)

    @setting(222, 'Set Heater Power', output_channel = 'i', power = 'v', returns = 'v')
    def heater_power(self, c, output_channel, power = None):
        """
        Set or query heater power.
        If heater is in manual mode, then heater directly controls power/current.
        If heater is in closed loop mode, then heater sets power/current offset for PID.
        Args:
            output_channel (int): the heater channel
            power (float): the heater power as aa percentage of max amount
        Returns:
            (float): the heater power
        """
        chString = 'MOUT'

        #todo: check for errors

        if power is not None:
            output_msg = ' ' + str(output_channel) + ',' + str(power) + TERMINATOR
            yield self.ser.write(chString + output_msg)

        #issue query
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield float(self.ser.read())
        returnValue(resp)

    @setting(223, 'Set Heater PID', output_channel = 'i', prop = 'v', int = 'v', diff = 'v', returns = 'v')
    def heater_PID(self, c, output_channel, prop = None, int = None, diff = None):
        """
        Set or query heater PID parameters. Only available if heater is in PID mode.
        Args:
            output_channel (int): the heater channel
            prop           (float): Proportional
            int            (float): Integral
            diff           (float): Derivative
        Returns:
                            [float, float, float]: the PID parameters
        """
        chString = 'PID'

        #check for errors ***

        if all(vals != None for vals in [prop, int, diff]):
            output_msg = chString + ' ' + str(output_channel) + ',' + str(prop) + ',' + str(int) + ',' + str(diff) + TERMINATOR
            yield self.write(output_msg)

        #issue query
        resp = yield self.query(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = np.array(resp.split(','), dtype=float)
        returnValue(resp)

    @setting(230, 'Get Heater Output', output_channel = 'i', returns = 'v')
    def heater_output(self, c, output_channel):
        """
        Get the heater output in % of max. current
        Args:
            output_channel  (int): the heater channel
        Returns:
                            (float): the heater output
        """

        resp = yield self.query(chString + '? ' + str(output_channel) + TERMINATOR)
        returnValue(float(resp))

        #todo: autotune

if __name__ == '__main__':
    from labrad import util
    util.runServer(Lakeshore336Server())