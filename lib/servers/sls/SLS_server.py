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

TERMINATOR = '\r\n'

class SLSServer(SerialDeviceServer):
    name = 'SLS Server'
    regKey = 'SLSServer'
    serNode = 'causewaybay'
    port = 'COM'

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
        yield self.ser.write('get ' + chString + TERMINATOR)
        resp = yield self.ser.read()
        returnValue(resp)

    @setting(112, 'autolock status', returns='*v')
    def autolock_status(self, c, enable=None):
        '''
        Get autolock status
        '''
        chString = ['LockTime', 'LockCount', 'AutoLockState']
        resp = []
        for string in chString:
            yield self.ser.write('get ' + string + TERMINATOR)
            resp_tmp = yield self.ser.read()
            resp.append(resp_tmp)

        returnValue(resp)

    #PDH
    @setting(211, 'PDH', mod_freq = 'v', mod_ind = 'v', ref_phase = 'v', filter = 'i', returns = '*v')
    def PDH(self, c, mod_freq = None, mod_ind = None, ref_phase = None, filter = None):
        '''
        Adjust PDH settings
        '''
        #array of parameters
        params = [mod_freq, mod_ind, ref_phase, filter]
        chString = ['PDHFrequency', 'PDHPMIndex', 'PDHPhaseOffset', 'PDHPhaseNoOffset', 'PDHDemodFilter']
        resp = []

        #write and get immediately after each parameter
        for i in range(len(params)):
            #setters
            if params[i] is not None:
                yield self.ser.write('set ' + chString[i] + ' ' + params[i] + TERMINATOR)

            #getters
            yield self.ser.write('get ' + chString[i] + TERMINATOR)
            resp_tmp = yield self.ser.read()
            resp.append(resp_tmp)
        returnValue(resp)

    #Offset lock


    #Servo
    @setting(411, 'servo', param = 's', prop = 'v', int = 'v', diff = 'v', set = 'i', invert = 'b', filter = 'i', returns = '*v')
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
        chString = ['ServoPropGain', 'ServoIntGain', 'ServoPropGain', 'ServoInvertLoop', 'ServoOutputFilter']
        resp = []

        #write and get immediately after each parameter
        for i in range(len(params)):
            #setters
            if params[i] is not None:
                yield self.ser.write('set ' + param + chString[i] + ' ' + params[i] + TERMINATOR)

            #getters
            yield self.ser.write('get ' + param + chString[i] + TERMINATOR)
            resp_tmp = yield self.ser.read()
            resp.append(resp_tmp)
        returnValue(resp)

    #Misc. settings


if __name__ == "__main__":
    from labrad import util
    util.runServer(SLSServer())
