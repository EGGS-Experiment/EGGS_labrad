"""
### BEGIN NODE INFO
[info]
name = AMO1 Server
version = 1.0.0
description = Communicates with the AMO1 box for current control.
instancename = AMO1Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.units import WithUnit
from labrad.server import setting, Signal

from twisted.internet.defer import returnValue
from EGGS_labrad.servers import SerialDeviceServer

TERMINATOR = '\r\n'


class AMO1Server(SerialDeviceServer):
    """
    Communicates with the AMO1 box for current control.
    """

    name = 'AMO1 Server'
    regKey = 'AMO1Server'
    serNode = 'MongKok'
    port = 'COM25'

    timeout = WithUnit(3.0, 's')
    baudrate = 38400


    # SIGNALS
    toggle_update = Signal(999999, 'signal: toggle update', 'b')
    output_update = Signal(999998, 'signal: output update', '(vv)')
    current_update = Signal(999997, 'signal: current update', '(sv)')


    # CONTEXTS
    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f.
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)


    # STARTUP
    def initServer(self):
        super().initServer()
        self.listeners = set()


    # GENERAL
    @setting(12, 'Remote', remote_status='b')
    def remote(self, c, remote_status=None):
        """
        Set remote mode of device.
        Arguments:
            remote_status   (bool)  : whether the device accepts serial commands
        Returns:
                            (bool)  : whether the device accepts serial commands
        """
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
        # parse
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
        # setter
        if status is not None:
            yield self.ser.acquire()
            yield self.ser.write('out.w {:d}\r\n'.format(status))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('out.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse
        resp = resp.strip()
        resp = bool(int(resp))
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
        if curr_ma is not None:
            if (curr_ma < 0) or (curr_ma > 80):
                raise Exception("Error: set current must be in range (10, 35) mA.")
            yield self.ser.acquire()
            yield self.ser.write('iout.na.w {:f}\r\n'.format(curr_ma * 1e6))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('iout.na.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
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
            if (curr_ma < 0) or (curr_ma > 80):
                raise Exception("Error: max current must be in range (10, 35) mA.")
            yield self.ser.acquire()
            yield self.ser.write('iout.ma.w {:f}\r\n'.format(curr_ma))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('ilim.ma.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp.strip()) / 1e3
        self.notifyOtherListeners(c, ('SET', resp), self.current_update)
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(AMO1Server())
    