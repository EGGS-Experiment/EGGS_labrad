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

#imports
from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

import numpy as np
from serial import PARITY_ODD

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer


INPUT_CHANNELS = ['A', 'B', 'C', 'D', '0']
OUTPUT_CHANNELS = [1, 2, 3, 4]
TERMINATOR = '\r\n'

TEMPSIGNAL = 122485

class Lakeshore336Server(SerialDeviceServer):
    """Talks to the Lakeshore 336 Temperature Controller"""
    name = 'Lakeshore336 Server'
    regKey = 'Lakeshore336Server'
    serNode = 'MongKok'
    port = 'COM24'

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
    @setting(111, 'Read Temperature', channel='s', returns='*1v')
    def temperature_read(self, c, channel=None):
        """
        Get sensor temperature
        Args:
            channel (str): sensor channel to measure
        Returns:
            (*float): sensor temperature in Kelvin
        """
        if not channel:
            channel = '0'
        elif channel not in INPUT_CHANNELS:
            raise Exception('Invalid input: channel must be one of: ' + str(INPUT_CHANNELS))
        yield self.ser.write('KRDG? ' + str(channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        resp = np.array(resp.split(','), dtype=float)
        returnValue(tuple(resp))

    # HEATER
    @setting(211, 'Heater Setup', output_channel='i', resistance='i', max_current='v', returns='*v')
    def heater_setup(self, c, output_channel, resistance, max_current):
        """
        Set up the physical parameters of the heater.
        This shold be done after the heater mode is set.
        Args:
            output_channel  (int): the heater channel
            resistance      (int): the heater resistance setting (1 = 25 Ohms, 2 = 50 Ohms)
            max_current     (float): maximum heater output current
        Returns:
                            (int, float): (resistance, max_current)
        """
        chString = 'HTRSET'
        #setter
        output_msg = ' ' + str(output_channel) + ',' + str(resistance) + ',0,' + str(max_current) + ',1' + TERMINATOR
        yield self.ser.write(chString + output_msg)
        #getter
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        resp = resp.split(',')
        resp = [int(resp[1]), float(resp[2])]
        returnValue(resp)

    @setting(212, 'Heater Mode', output_channel='i', mode='i', input_channel='i', returns='(ii)')
    def heater_mode(self, c, output_channel, mode, input_channel):
        """
        Set the output mode of the heater.
        Args:
            output_channel  (int): the heater channel
            mode            (int): heater operation mode (0=off, 1=PID, 2=zone, 3=open loop,
                                                        4=monitor out, 5=warmup)
            input_channel   (str): the temperature diode channel to control the output
        Returns:
                            (int, int): the output mode and linked input channel
        """
        chString = 'OUTMODE'
        #setter
        output_msg = chString + ' ' + str(output_channel) + ',' + str(mode) + ',' + str(input_channel) + ',0' + TERMINATOR
        yield self.ser.write(output_msg)
        #getter
        yield self.ser.write(chString + '?' + str(output_channel) + ' ' + TERMINATOR)
        resp = yield self.ser.read_line()
        resp = np.array(resp.split(','), dtype=int)
        resp = tuple(resp[:2])
        returnValue(resp)

    @setting(221, 'Heater Range', output_channel='i', range='i', returns='i')
    def heater_range(self, c, output_channel, range):
        """
        Set or query heater range.
        Args:
            output_channel  (int): the heater channel
            range           (int): the heater range (0=off, 1=1% of max, 2=10% of max, 3=100% of max)
        Returns:
            (int): the heater range
        """
        chString = 'RANGE'
        #setter
        output_msg = ' ' + str(output_channel) + ',' + str(range) + TERMINATOR
        yield self.ser.write(chString + output_msg)
        #getter
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        returnValue(int(resp))

    @setting(213, 'Heater Power', output_channel='i', power='v', returns='v')
    def heater_power(self, c, output_channel, power):
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
        #setter
        output_msg = ' ' + str(output_channel) + ',' + str(power) + TERMINATOR
        yield self.ser.write(chString + output_msg)
        #getter
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        returnValue(float(resp))


    @setting(231, 'Heater PID', output_channel='i', prop='v', int='v', diff='v', returns='(vvv)')
    def heater_PID(self, c, output_channel, prop=None, int=None, diff=None):
        """
        Set or query heater PID parameters. Only available if heater is in PID mode.
        Args:
            output_channel (int): the heater channel
            prop           (float): Proportional
            int            (float): Integral
            diff           (float): Derivative
        Returns:
                            (float, float, float): the PID parameters
        """
        chString = 'PID'
        if all(vals != None for vals in [prop, int, diff]):
            output_msg = chString + ' ' + str(output_channel) + ',' + str(prop) + ',' + str(int) + ',' + str(diff) + TERMINATOR
            yield self.write(output_msg)
        #issue query
        resp = yield self.query(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = np.array(resp.split(','), dtype=float)
        returnValue(tuple(resp))

    @setting(232, 'Heater Setpoint', output_channel='i', setpoint='v', returns='v')
    def heater_setpoint(self, c, output_channel, setpoint):
        """
        Set the heater setpoint in closed-loop output mode.
        Args:
            output_channel  (int): the heater channel
            setpoint        (float): the setpoint (in Kelvin)
        Returns:
                            (float): the setpoint (in Kelvin)
        """
        chString = 'SETP'
        #setter
        output_msg = chString + ' ' + str(output_channel) + ',' + str(setpoint) + TERMINATOR
        yield self.write(output_msg)
        #getter
        yield self.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = self.read_line()
        returnValue(float(resp))

    @setting(241, 'Heater Autotune', output_channel='i', input_channel='i', mode='i', returns='*1v')
    def heater_autotune(self, c, output_channel, input_channel, mode):
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
        #setter
        output_msg = ' ' + str(output_channel) + ',' + str(resistance) + ',0,' + str(max_current) + ',2' + TERMINATOR
        yield self.ser.write(chString + output_msg)
        #getter
        yield self.ser.write(chString + '? ' + str(output_channel) + TERMINATOR)
        resp = yield self.ser.read_line()
        resp = resp.split(',')
        resp = [int(resp[1]), float(resp[2])]
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(Lakeshore336Server())