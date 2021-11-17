"""
### BEGIN NODE INFO
[info]
name = NIOPS03 Server
version = 1.0.0
description = Controls NIOPS-03 Power Supply which controls ion pumps
instancename = NIOPS03 Server

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
from labrad.server import setting
from labrad.support import getNodeName
from labrad.units import WithUnit
import numpy as np

TERMINATOR = '\r\n'
QUERY_msg = b'\x05'

class NIOPS03Server(SerialDeviceServer):
    """Controls NIOPS-03 Power Supply which controls ion pumps"""
    name = 'NIOPS03 Server'
    regKey = 'NIOPS03Server'
    serNode = 'CausewayBay'
    port = 'COM8'

    timeout = WithUnit(3.0, 's')
    baudrate = 115200

    #STATUS
    @setting(11,'Status', returns='s')
    def get_status(self, c):
        """
        Get controller status
        Returns:
            (str): which switches and alarms are on/off
        """
        yield self.ser.write('TS' + TERMINATOR)
        resp = yield self.ser.read()
        return resp

    # ON/OFF
    @setting(111,'Toggle IP', power='b', returns='s')
    def toggle_ip(self, c, power = None):
        """
        Set or query whether ion pump is off or on
        Args:
            (bool): whether pump is to be on or off
        Returns:
            (float): pump power status
        """
        if power == True:
            yield self.ser.write('G' + TERMINATOR)
        elif power == False:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read()
        resp = resp.strip()
        return resp

    @setting(112, 'Toggle NP', power='b')
    def toggle_np(self, c, power = None):
        """
        Set or query whether getter is off or on
        Args:
            (bool): whether getter is to be on or off
        Returns:
            (bool): getter power status
        """
        if power == True:
            yield self.ser.write('GN' + TERMINATOR)
        elif power == False:
            yield self.ser.write('BN' + TERMINATOR)
        resp = yield self.ser.read()
        return resp

    #PARAMETERS
    @setting(211,'IP Pressure', returns='v')
    def pressure_ip(self, c):
        """
        Get ion pump pressure in mbar
        Returns:
            (float): ion pump pressure
        """
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)

    @setting(221, 'IP Voltage', voltage='v', returns='v')
    def voltage_ip(self, c, voltage=None):
        """
        Get/set ion pump voltage
        Arguments:
            voltage (float) : pump voltage in V
        Returns:
                    (float): ion pump voltage in V
        """
        if voltage:
            #convert voltage to hex
            voltage = hex(voltage)[2:]
            padleft = '0'*(4-len(voltage))
            yield self.ser.write('u' + padleft + voltage + TERMINATOR)
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read()
        #convert from hex to int
        resp = int(resp, 16)
        returnValue(resp)

    @setting(231, 'Working Time', returns='*2i')
    def working_time(self, c):
        """
        Gets working time of IP & NP
        Returns:
            [[int, int], [int, int]]: getter voltage
        """
        yield self.ser.write('TM' + TERMINATOR)
        ip_time = yield self.ser.read()
        np_time = yield self.ser.read()
        ip_time = ip_time[16:-8].split(' Hours ')
        np_time = np_time[16:-8].split(' Hours ')
        ip_time = [int(val) for val in ip_time]
        np_time = [int(val) for val in np_time]
        returnValue([ip_time, np_time])

if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())