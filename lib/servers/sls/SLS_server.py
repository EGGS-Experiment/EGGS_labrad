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
    name = 'SLS Server'
    regKey = 'SLSServer'
    serNode = 'causewaybay'
    port = 'COM5'

    baudrate = 115200
    timeout = T.Value(1.0, 's')

    #Autolock
    @setting(111,'autolock toggle', enable = 's', returns = 's')
    def autolock_toggle(self, c, enable = None):
        '''
        Toggle autolock
        '''
        chString = 'AutoLockEnable'
        #setters
        if enable is not None:
            yield self.ser.write('set ' + chString + ' ' + enable + TERMINATOR)

        #getters
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

    #PDH
    @setting(211, 'PDH', mod_freq = 'v', mod_ind = 'v', ref_phase = 'v', filter = 'i', returns = '*s')
    def PDH(self, c, mod_freq = None, mod_ind = None, ref_phase = None, filter = None):
        '''
        Adjust PDH settings
        '''
        #array of parameters
        params = [mod_freq, mod_ind, ref_phase, filter]
        #chString = ['PDHFrequency', 'PDHPMIndex', 'PDHPhaseOffset', 'PDHPhaseNoOffset', 'PDHDemodFilter']
        chString = ['PDHFrequency', 'PDHPMIndex', 'PDHPhaseOffset', 'PDHDemodFilter']
        resp = []

        #write and get immediately after each parameter
        for i in range(len(params)):
            #setters
            if params[i] is not None:
                yield self.ser.write('set ' + chString[i] + ' ' + params[i] + TERMINATOR)
            #getters
            resp_tmp = yield self._getValue(chString[i])
            resp.append(resp_tmp)
        returnValue(resp)

    #Offset lock


    #Servo
    @setting(411, 'servo', param = 's', prop = 'v', int = 'v', diff = 'v', set = 'i', invert = 'b', filter = 'i', returns = '*s')
    def servo(self, c, param, prop = None, int = None, diff = None, set = None, invert = None, filter = None):
        '''
        Adjust PID servo for given parameter
        '''
        #check parameter has been specified
        if type(param) == str:
            param = param.upper()
            #check parameter is valid
            if param == 'CURRENT':
                param = 'Current'
            elif param != ('PZT' and 'TX'):
                raise Exception("Invalid parameter")
        else:
            raise Exception("Specify parameter to servo")

        #array of parameters
        params = [prop, int, diff, set, invert, filter]
        chString = ['ServoPropGain', 'ServoIntGain', 'ServoDiffGain', 'ServoSetpoint', 'ServoInvertLoop', 'ServoOutputFilter']
        chString = [param + string for string in chString]
        resp = []

        #write and get immediately after each parameter
        for i in range(len(params)):
            #setters
            if params[i] is not None:
                yield self.ser.write('set ' + chString[i] + ' ' + params[i] + TERMINATOR)
            #getters
            resp_tmp = yield self._getValue(chString[i])
            resp.append(resp_tmp)
        returnValue(resp)

    #Misc. settings

    #Helper functions
    @inlineCallbacks
    def _getValue(self, string):
        echo_length = yield self.ser.write('get ' + string + TERMINATOR)
        #echo_length += len(string)
        sleep(0.5)
        resp = yield self.ser.read()
        resp = resp[echo_length:STRIP_END]
        returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(SLSServer())
