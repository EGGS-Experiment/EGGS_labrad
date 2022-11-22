"""
### BEGIN NODE INFO
[info]
name = AMO3 Server
version = 1.0.0
description = Communicates with the AMO3 box for control of piezo voltages.
instancename = AMO3 Server

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
from EGGS_labrad.servers import SerialDeviceServer

TERMINATOR = '\r\n'


class AMO3Server(SerialDeviceServer):
    """
    Communicates with the AMO3 box for control of piezo voltages.
    """

    name = 'AMO3 Server'
    regKey = 'AMO3Server'
    serNode = 'MongKok'
    port = 'COM10'

    timeout = WithUnit(3.0, 's')
    baudrate = 38400


    # SIGNALS
    voltage_update = Signal(999999, 'signal: voltage update', '(iv)')
    toggle_update = Signal(999998, 'signal: toggle update', '(ib)')

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


    # ON/OFF
    @setting(111, 'Toggle', channel='i', power='i', returns='b')
    def toggle(self, c, channel, power=None):
        """
        Set a channel to be on or off.
        Args:
            channel (int)   : the channel to read/write.
            power   (bool)  : whether channel is to be on or off
        Returns:
                    (bool)  : result
        """
        if channel not in (1, 2, 3, 4):
            raise Exception("Error: channel must be one of (1, 2, 3, 4).")
        # setter
        if power is not None:
            yield self.ser.acquire()
            yield self.ser.write('out.w {:d} {:d}\r\n'.format(channel, power))
            yield self.ser.read_line('\n')
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write('out.r {:d}\r\n'.format(channel))
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        # parse
        resp = resp.strip()
        resp = bool(int(resp))
        self.notifyOtherListeners(c, (channel, resp), self.toggle_update)
        returnValue(resp)


    # VOLTAGE
    @setting(211, 'Voltage', channel='i', voltage='v', returns='v')
    def voltage(self, c, channel, voltage=None):
        """
        Sets/get the channel voltage.
        Arguments:
            channel (int)   : the channel to read/write
            voltage (float) : the channel voltage to set
        Returns:
                    (float) : the channel voltage
        """
        # setter
        if channel not in (1, 2, 3, 4):
            raise Exception("Error: channel must be one of (1, 2, 3, 4).")
        if voltage is not None:
            if (voltage < 0) or (voltage > 150):
                raise Exception("Error: voltage must be in [0, 150].")
            yield self.ser.acquire()
            yield self.ser.write('vout.w {:d} {:3f}\r\n'.format(channel, voltage))
            yield self.ser.read_line('\n')
            self.ser.release()
        # getter
        yield self.ser.acquire()
        yield self.ser.write('vout.r {:d}\r\n'.format(channel))
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = float(resp)
        self.notifyOtherListeners(c, (channel, resp), self.voltage_update)
        returnValue(float(resp))


if __name__ == '__main__':
    from labrad import util
    util.runServer(AMO3Server())
    