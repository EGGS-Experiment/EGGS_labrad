"""
### BEGIN NODE INFO
[info]
name = Injection Lock Current Server
version = 1.0.0
description = Communicates with the current controller box for injection lock diode
instancename = Injection Lock Current Server

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

from twisted.internet.defer import returnValue
from EGGS_labrad.servers import SerialDeviceServer, PollingServer
import time

TERMINATOR = '\r\n'
# note: why current_update is (sv)? why does it need a string message?
# note: same for max_curr update? why need str?


class InjectionLockCurrentServer(SerialDeviceServer, PollingServer):
    """
    Communicates with the current controller box for the injection lock diode
    """

    name = 'Injection Lock Current Server'
    regKey = 'InjectionLockCurrentServer'
    serNode = 'HengFaChuen'
    port = 'COM5'
    timeout = WithUnit(3.0, 's')
    baudrate = 38400

    # SIGNALS
    toggle_update = Signal(999969, 'signal: toggle update', 'b')
    output_update = Signal(999968, 'signal: output update', '(vv)')
    current_update = Signal(999967, 'signal: current update', '(sv)')
    max_current_update = Signal(999966, 'signal: max current update', '(sv)')

    # GENERAL
    @setting(12, 'Remote', remote_status='b')
    def remote(self, c, remote_status=None):
        """
        Get/set remote mode of device.
        Arguments:
            remote_status   (bool)  : whether the device accepts serial commands.
        Returns:
                            (bool)  : whether the device accepts serial commands.
        """
        # setter
        if remote_status is not None:
            yield self.ser.acquire()
            yield self.ser.write('remote.w {:d}\r\n'.format(remote_status))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('remote.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse response
        resp = bool(int(resp.strip()))
        returnValue(resp)


    # STATUS
    @setting(111, 'Toggle', status='i', returns='b')
    def toggle(self, c, status=None):
        """
        Enable/disable output.
        Arguments:
            status  (bool): whether output is enabled or not.
        Returns:
                    (bool): the output status.
        """
        # todo: accept true/false or 1/0
        # setter
        if status is not None:
            yield self.ser.acquire()
            yield self.ser.write('out.w {:d}\r\n'.format(status))
            message = yield self.ser.read_line('\n')
            self.ser.release()

            # let device update
            time.sleep(0.1)

        # getter
        yield self.ser.acquire()
        yield self.ser.write('out.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse response and update other clients
        resp = bool(int(resp.strip()))
        self.notifyOtherListeners(c, resp, self.toggle_update)
        returnValue(resp)

    @setting(121, 'Outputs', returns='(vv)')
    def outputs(self, c):
        """
        Get the diode outputs.
        Returns:
            tuple(float, float): the diode voltage (in V) and current (in A).
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('diode.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse
        resp = resp.strip().split(', ')
        resp = tuple([float(val[:-1]) for val in resp])
        self.notifyOtherListeners(c, resp, self.output_update)
        returnValue(resp)

    # CURRENT
    @setting(211, 'Current Set', curr_ma='v', returns='v')
    def currentSet(self, c, curr_ma=None):
        """
        Get/set the set output current.
        Arguments:
            curr_ma (float) : the output current (in mA).
        Returns:
                    (float) : the output current (in mA).
        """
        # setter
        try:
            curr_ma_max = yield self.currentMax(None)
        except Exception as e:
            curr_ma_max = 100
        if curr_ma is not None:
            if (curr_ma < 10) or (curr_ma > curr_ma_max):
                raise Exception("Error: set current must be in range [10, 100] mA.")
            yield self.ser.acquire()
            yield self.ser.write('iout.na.w {:f}\r\n'.format(curr_ma * 1e6))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('iout.na.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse response and update other clients
        resp = float(resp.strip()) / 1e6
        self.notifyOtherListeners(c, ('SET', resp), self.current_update)
        returnValue(resp)

    @setting(222, 'Current Max', curr_ma='v', returns='v')
    def currentMax(self, c, curr_ma=None):
        """
        Get/set the maximum output current.
        Arguments:
            curr_ma (float) : the maximum output current (in mA).
        Returns:
                    (float) : the maximum output current (in mA).
        """
        # setter
        if curr_ma is not None:
            if (curr_ma < 10) or (curr_ma > 100):
                raise Exception("Error: max current must be in range [10, 100] mA.")
            yield self.ser.acquire()
            yield self.ser.write('ilim.ma.w {:f}\r\n'.format(curr_ma))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('ilim.ma.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse response and update other clients
        resp = float(resp.strip())
        self.notifyOtherListeners(c, ('SET', resp), self.max_current_update)
        returnValue(resp)

    @inlineCallbacks
    def _poll(self):
        yield self.toggle(None, None)
        yield self.outputs(None)
        yield self.currentSet(None, None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(InjectionLockCurrentServer())
