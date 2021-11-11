"""
### BEGIN NODE INFO
[info]
name = SLS Server
version = 1.0
description =
instancename = SLS Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
#todo: check and sanitize input for each setting
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad import types as T
from twisted.internet.defer import returnValue
from labrad.support import getNodeName

from time import sleep

TERMINATOR = '\r\n'
STRIP_END = -8

class SLSServer(SerialDeviceServer):
    """Connects to the 729nm SLS Laser"""
    name = 'SLS Server'
    regKey = 'SLSServer'
    serNode = 'causewaybay'
    port = 'COM5'

    baudrate = 115200
    timeout = T.Value(1.0, 's')

    #Autolock
    @setting(111,'autolock toggle', enable='s', returns='s')
    def autolock_toggle(self, c, enable=None):
        '''
        Toggle autolock
        '''
        chString = 'AutoLockEnable'
        if enable:
            yield self.ser.write('set ' + chString + ' ' + enable + TERMINATOR)

        resp = yield self._getValue(chString)
        returnValue(resp)

    @setting(112, 'autolock status', returns='*s')
    def autolock_status(self, c):
        '''
        Get autolock status
        '''
        chString = ['LockTime', 'LockCount', 'AutoLockState']
        resp = []
        for string in chString:
            resp_tmp = yield self._getValue(string)
            resp.append(resp_tmp)
        returnValue(resp)

    @setting(111,'autolock parameter', param='s', returns = 's')
    def autolock_param(self, c, param=None):
        '''
        Choose parameter for autolock to sweep
        '''
        chString = 'SweepType'
        if param.lower() == 'current':
            yield self.ser.write('set ' + chString + ' ' + '2' + TERMINATOR)
        if param.upper() == 'PZT':
            yield self.ser.write('set ' + chString + ' ' + '1' + TERMINATOR)
        resp = yield self._getValue(chString)
        returnValue(resp)

    #PDH
    @setting(211, 'PDH', param_name = 's', param_val = '?', returns = 's')
    def PDH(self, c, param_name, param_val = None):
        '''
        Adjust PDH settings
        Arguments:
            param_name      (string): the parameter to adjust, can be 'frequency', 'index', 'phase', or 'filter'
            param_val       (): the value to set the parameter to

        '''
        chstring = {'frequency': 'PDHFrequency', 'index': 'PDHPMIndex', 'phase': 'PDHPhaseOffset', 'filter': 'PDHDemodFilter'}
        string_tmp = chstring[param_name.lower()]
        if param_val:
            yield self.ser.write('set ' + string_tmp + ' ' + param_val + TERMINATOR)
        resp = yield self._getValue(string_tmp)
        returnValue(resp)

    #Offset lock


    #Servo
    @setting(411, 'servo', servo_target='s', param_name='s', param_val='?', returns='s')
    def servo(self, c, servo_target, param_name, param_val=None):
        '''
        Adjust PID servo for given parameter
        Arguments:
            servo_target    (string): target of the PID lock
            param_name      (string): the parameter to change
            param_val       (): value to change
        '''
        tgstring = {'current': 'Current', 'pzt': 'PZT', 'tx': 'TX'}
        chstring = {'p': 'ServoPropGain', 'i': 'ServoIntGain', 'd': 'ServoDiffGain', 'set': 'ServoSetpoint', 'loop': 'ServoInvertLoop', 'filter': 'ServoOutputFilter'}

        string_tmp = tgstring[servo_target.lower()] + chstring[param_name.lower()]
        if param_val is not None:
            yield self.ser.write('set ' + string_tmp + ' ' + param_val + TERMINATOR)
        resp = yield self._getValue(string_tmp)
        returnValue(resp)

    #Misc. settings

    #Helper functions
    @inlineCallbacks
    def _getValue(self, string):
        """
        Strips the echo from the SLS
        """
        echo_length = yield self.ser.write('get ' + string + TERMINATOR)
        #echo_length += len(string)
        sleep(0.5)
        resp = yield self.ser.read()
        resp = resp[echo_length:STRIP_END]
        returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(SLSServer())
