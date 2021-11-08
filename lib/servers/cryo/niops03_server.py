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
    serNode = 'causewaybay'
    port = 'COM4'

    timeout = WithUnit(3.0, 's')
    baudrate = 115200

    #STATUS
    @setting(11,'Status', returns = 's')
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
    @setting(111,'Toggle IP', power = 'b', returns = 's')
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

    @setting(112,'Toggle NP', power = 'b')
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
    @setting(211,'Get IP Pressure', returns = 'v')
    def get_pressure_ip(self, c):
        """
        Get ion pump pressure
        Returns:
            (float): ion pump pressure
        """
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)

    @setting(221,'Get IP Voltage', returns = 'v')
    def get_voltage_ip(self, c):
        """
        Get ion pump voltage
        Returns:
            (float): ion pump voltage
        """
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read()
        return float(resp)

    @setting(231,'Get Working Time', returns = 's')
    def get_time_working(self, c):
        """
        Gets working time of IP & NP
        Returns:
            (float): getter voltage
        """
        yield self.ser.write('TM' + TERMINATOR)
        resp = yield self.ser.read()
        return resp
        #todo: get multiple lines


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())