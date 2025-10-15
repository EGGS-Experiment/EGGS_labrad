"""
### BEGIN NODE INFO
[info]
name = Injection Lock Temperature Server
version = 1.0.0
description = Communicates with the AMO2 box for control of TECs.
instancename = Injection Lock Temperature Server

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
from EGGS_labrad.servers import SerialDeviceServer, PollingServer, ContextServer

TERMINATOR = '\r\n'


class InjectionLockTemperatureServer(SerialDeviceServer, PollingServer):
    """
    Communicates with the AMO2 box for control of TECs.
    """

    name = 'Injection Lock Temperature Server'
    regKey = 'InjectionLockTemperatureServer'
    serNode = 'HengFaChuen'
    port = 'COM6'

    timeout = WithUnit(3.0, 's')
    baudrate = 38400


    # SIGNALS
    toggle_update = Signal(999999, 'signal: toggle update', 'b')
    current_update = Signal(999998, 'signal: current update', 'v')
    temperature_update = Signal(999997, 'signal: temperature update', 'v')
    lock_update = Signal(999996, 'signal: lock update', '(sv)')
    setpoint_update = Signal(999995, 'signal: setpoint update', '(v)')


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

    @setting(121, 'Current', returns='v')
    def current(self, c):
        """
        Get the instantaneous output current.
        Returns:
            (float): the output current.
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('iout.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse
        resp = float(resp.strip())
        self.current_update(resp)
        returnValue(resp)

    @setting(122, 'Temperature', returns='v')
    def temperature(self, c):
        """
        Get the sensor temperature.
        Returns:
            (float): the sensor temperature.
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('tempsensor.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse
        resp = float(resp[:-2])
        self.temperature_update(resp)
        returnValue(resp)


    # LOCKING
    @setting(211, 'Locking Setpoint', temp='v', returns='v')
    def lockingSetpoint(self, c, temp=None):
        """
        Get/set the temperature setpoint.
        Arguments:
            temp    (float): the temperature setpoint.
        Returns:
                    (float): the temperature setpoint.
        """
        # setter
        if temp is not None:
            if (temp < 10) or (temp > 35):
                raise Exception("Error: set temperature must be in range (10, 35).")
            yield self.ser.acquire()
            yield self.ser.write('temp.w {:f}\r\n'.format(temp))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('temp.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp[:-2])
        self.notifyOtherListeners(c, resp, self.setpoint_update)
        # todo: notify other listeners
        returnValue(resp)

    @setting(221, 'Locking P', prop='v', returns='v')
    def lockingP(self, c, prop=None):
        """
        Get/set the proportional parameter (in machine units).
        Arguments:
            prop    (float): the proportional parameter (in machine units).
        Returns:
                    (float): the proportional parameter (in machine units).
        """
        # setter
        if prop is not None:
            if (prop < 0) or (prop > 255):
                raise Exception("Error: proportional parameter must be in range (0, 255).")
            yield self.ser.acquire()
            yield self.ser.write('p.w {:f}\r\n'.format(prop))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('p.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp.strip())
        # todo: notify other listeners
        returnValue(resp)

    @setting(222, 'Locking I', integ='v', returns='v')
    def lockingI(self, c, integ=None):
        """
        Get/set the integral parameter (in machine units).
        Arguments:
            integ   (float): the integral parameter (in machine units).
        Returns:
                    (float): the integral parameter (in machine units).
        """
        # setter
        if integ is not None:
            if (integ < 0) or (integ > 255):
                raise Exception("Error: integral parameter must be in range (0, 255).")
            yield self.ser.acquire()
            yield self.ser.write('i.w {:f}\r\n'.format(integ))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('i.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp.strip())
        # todo: notify other listeners
        returnValue(resp)

    @setting(223, 'Locking D', deriv='v', returns='v')
    def lockingD(self, c, deriv=None):
        """
        Get/set the derivative parameter (in machine units).
        Arguments:
            deriv   (float): the derivative parameter (in machine units).
        Returns:
                    (float): the derivative parameter (in machine units).
        """
        # setter
        if deriv is not None:
            if (deriv < 0) or (deriv > 255):
                raise Exception("Error: derivative parameter must be in range (0, 255).")
            yield self.ser.acquire()
            yield self.ser.write('d.w {:f}\r\n'.format(deriv))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('d.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp.strip())
        # todo: notify other listeners
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for temperature and current readout and other params
        """
        yield self.temperature(None)
        yield self.current(None)
        yield self.lockingSetpoint(None)
        yield self.lockingP(None)
        yield self.lockingI(None)
        yield self.lockingD(None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(InjectionLockTemperatureServer())
