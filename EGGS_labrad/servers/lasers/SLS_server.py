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

from labrad.units import Value
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.servers import PollingServer, SerialDeviceServer

TERMINATOR = '\r\n'
_SLS_EOL = '>'


class SLSServer(SerialDeviceServer, PollingServer):
    """
    Connects to the 729nm SLS Laser.
    """

    name = 'SLS Server'
    regKey = 'SLS Server'
    serNode = 'mongkok'
    port = 'COM4'

    baudrate = 115200
    timeout = Value(5.0, 's')

    # SIGNALS
    autolock_update = Signal(999999, 'signal: autolock update', '(iv)')


    # AUTOLOCK
    @setting(111, 'Autolock Toggle', enable='s', returns='s')
    def autolock_toggle(self, c, enable=None):
        """
        Toggle autolock.
        """
        chString = 'AutoLockEnable'
        resp = yield self._write_and_query(chString, enable)
        returnValue(resp)

    @setting(112, 'Autolock Status', returns='*s')
    def autolock_status(self, c):
        """
        Get autolock status.
        Returns:
            [v, v, v]: the lock time, lock count, and lock state
        """
        chString = ['LockTime', 'LockCount', 'AutoLockState']
        resp = []
        for string in chString:
            # query
            yield self.ser.acquire()
            resp_tmp = yield self.ser.write('get ' + string + TERMINATOR)
            resp_tmp = yield self.ser.read_line(_SLS_EOL)
            self.ser.release()
            # parse
            resp_tmp = yield self._parse(resp_tmp, False)
            resp.append(resp_tmp)
        returnValue(resp)

    @setting(113, 'Autolock Parameter', param='s', returns='s')
    def autolock_param(self, c, param=None):
        """
        Choose parameter for autolock to sweep.
        """
        chString = 'SweepType'
        tgstring = {'OFF': '0', 'PZT': '1', 'CURRENT': '2'}
        param_tg = None
        if param:
            try:
                param_tg = tgstring[param.upper()]
            except KeyError:
                print('Invalid parameter: parameter must be one of [\'OFF\', \'PZT\', \'CURRENT\']')
        resp = yield self._write_and_query(chString, param_tg)
        returnValue(resp)

    # PDH
    @setting(211, 'PDH', param_name='s', param_val='?', returns='s')
    def PDH(self, c, param_name, param_val=None):
        """
        Adjust PDH settings
        Arguments:
            param_name      (string): the parameter to adjust, can be any of ['frequency', 'index', 'phase', 'filter']
            param_val       ()      : the value to set the parameter to
        Returns:
                                    : the value of param_name
        """
        chstring = {'frequency': 'PDHFrequency', 'index': 'PDHPMIndex', 'phase': 'PDHPhaseOffset', 'filter': 'PDHDemodFilter'}
        try:
            string_tmp = chstring[param_name.lower()]
        except KeyError:
            print('Invalid parameter. Parameter must be one of [\'frequency\', \'index\', \'phase\', \'filter\']')
        if param_val:
            # setter
            yield self.ser.acquire()
            yield self.ser.write('set ' + string_tmp + ' ' + param_val + TERMINATOR)
            set_resp = yield self.ser.read_line(_SLS_EOL)
            self.ser.release()
            set_resp = yield self._parse(set_resp, True)
        # getter
        yield self.ser.acquire()
        yield self.ser.write('get ' + string_tmp + TERMINATOR)
        resp = yield self.ser.read_line(_SLS_EOL)
        self.ser.release()
        # return value
        resp = yield self._parse(resp, False)
        returnValue(resp)

    # OFFSET
    @setting(311, 'Offset Frequency', freq='v', returns='v')
    def offset_frequency(self, c, freq=None):
        """
        Set/get offset frequency.
        Arguments:
            freq    (float) : a frequency between [1e7, 8e8]
        Returns:
                    (float) : the value of offset frequency
        """
        chString = 'OffsetFrequency'
        resp = yield self._write_and_query(chString, freq)
        returnValue(float(resp))

    @setting(312, 'Offset Lockpoint', lockpoint='i', returns='i')
    def offset_lockpoint(self, c, lockpoint=None):
        """
        Set offset lockpoint.
        Arguments:
            lockpoint   (float) : offset lockpoint between [0, 4]. 0
        Returns:
                                : the offset lockpoint
        """
        chString = 'LockPoint'
        resp = yield self._write_and_query(chString, lockpoint)
        returnValue(int(resp))


    # SERVO
    @setting(411, 'servo', servo_target='s', param_name='s', param_val='?', returns='s')
    def servo(self, c, servo_target, param_name, param_val=None):
        """
        Adjust PID servo for given parameter.
        Arguments:
            servo_target    (string): target of the PID lock
            param_name      (string): the parameter to change
            param_val       ()      : value to change
        """
        tgstring = {'current': 'Current', 'pzt': 'PZT', 'tx': 'TX'}
        chstring = {'p': 'ServoPropGain', 'i': 'ServoIntGain', 'd': 'ServoDiffGain', 'set': 'ServoSetpoint',
                    'loop': 'ServoInvertLoop', 'filter': 'ServoOutputFilter'}
        try:
            string_tmp = tgstring[servo_target.lower()] + chstring[param_name.lower()]
        except KeyError:
            print('Invalid target or parameter. Target must be one of [\'current\',\'pzt\',\'tx\'].'
                  'Parameter must be one of [\'frequency\', \'index\', \'phase\', \'filter\']')
        resp = yield self._write_and_query(string_tmp, param_val)
        returnValue(resp)


    # MISC
    @setting(511, 'Get Values', returns='*2s')
    def get_values(self, c):
        """
        Returns the values of ALL parameters.
        """
        yield self.ser.acquire()
        yield self.ser.write_line('get values')
        resp = yield self.ser.read_line(_SLS_EOL)
        self.ser.release()
        # parse response
        resp = resp.split('\r\n')[2:-2]
        resp = [val.split('=') for val in resp]
        # return keys and values
        keys = [val[0] for val in resp]
        values = [val[1] for val in resp]
        returnValue((keys, values))


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for locking readout.
        """
        yield self.ser.acquire()
        yield self.ser.write('get LockCount' + TERMINATOR)
        lockcount = yield self.ser.read_line(_SLS_EOL)
        lockcount = yield self._parse(lockcount, False)
        yield self.ser.write('get LockTime' + TERMINATOR)
        locktime = yield self.ser.read_line(_SLS_EOL)
        locktime = yield self._parse(locktime, False)
        self.ser.release()
        self.autolock_update((int(lockcount), float(locktime)))


    # HELPERS
    def _parse(self, string, setter):
        """
        Strips echo from SLS and returns a dictionary with
        keys as parameter names and values as parameter value.
        """
        # result = {}
        if type(string) == bytes:
            string = string.decode('utf-8')
        # split by lines
        string = string.split('\r\n')
        # remove echo and end message
        string = string[1:-1]
        # setter responses only give ok or not ok
        if setter:
            return string
        # split parameters and values by '=' sign
        # for paramstring in string:
        #     params = paramstring.split('=')
        #     result[params[0]] = params[1]
        # print(string)
        params = string[0].split('=')
        return params[1]

    @inlineCallbacks
    def _write_and_query(self, chstring, param):
        """
        Writes parameter to SLS and verifies setting,
        then reads back same parameter.
        """
        if param:
            # write data and read echo
            yield self.ser.acquire()
            yield self.ser.write('set ' + chstring + ' ' + str(param) + TERMINATOR)
            set_resp = yield self.ser.read_line(_SLS_EOL)
            self.ser.release()
            # parse
            set_resp = yield self._parse(set_resp, True)
        # write data and read echo
        yield self.ser.acquire()
        yield self.ser.write('get ' + chstring + TERMINATOR)
        resp = yield self.ser.read_line(_SLS_EOL)
        self.ser.release()
        # parse
        resp = yield self._parse(resp, False)
        returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(SLSServer())
