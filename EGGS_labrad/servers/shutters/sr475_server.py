"""
### BEGIN NODE INFO
[info]
name = SR475 Server
version = 1.0.0
description = Controls the SR475 Shutter.
instancename = SR475 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.units import WithUnit
from labrad.server import setting
from twisted.internet.defer import returnValue

from EGGS_labrad.servers import SerialDeviceServer

TERMINATOR = ''


class SR475Server(SerialDeviceServer):
    """
    Controls the SR475 Shutter.
    """

    name = 'SR475 Server'
    regKey = 'SR475Server'
    serNode = None
    port = None

    timeout = WithUnit(5.0, 's')
    baudrate = 19200


    # CORE
    @setting(11, 'Reset', returns='')
    def reset(self, c):
        """
        Reset laser shutter. All values are set to default.
        """
        yield self.ser.acquire()
        yield self.ser.write('C')
        self.ser.release()

    @setting(12, 'Standby', returns='')
    def standby(self, c):
        """
        Turns off laser shutter. Puts shutter into indeterminate state.
        Reactivate shutter by doing a reset.
        """
        yield self.ser.acquire()
        yield self.ser.write('K')
        self.ser.release()

    @setting(13, 'Errors', returns='*s')
    def standby(self, c):
        """
        Get errors.
        Returns:
        """
        yield self.ser.acquire()
        yield self.ser.write('W')
        err = yield self.ser.read_line('\n')
        self.ser.release()
        # todo: finish


    # SHUTTER
    @setting(211, 'Shutter Set', state='b', returns='i')
    def shutterSet(self, c, state=None):
        """
        Set shutter state exactly.
        Arguments:
            state   (bool)  : open/close state of the shutter
        Returns:
                    (bool)  : shutter state
        """
        # set state
        if state is not None:
            yield self.ser.acquire()
            if state:
                yield self.ser.write('@')
            else:
                yield self.ser.write('A')
            self.ser.release()
        # get state
        yield self.ser.acquire()
        yield self.ser.write('S')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        if resp == '1':
            returnValue(1)
        elif resp == '0':
            returnValue(0)
        else:
            print('Error: shutter position is indeterminate.')

    @setting(212, 'Shutter Toggle', returns='b')
    def shutterToggle(self, c):
        """
        Toggle shutter state.
        Returns:
                (bool)   : shutter state
        """
        # toggle state
        yield self.ser.acquire()
        yield self.ser.write('B')
        self.ser.release()
        # get state
        yield self.ser.acquire()
        yield self.ser.write('S')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        if resp == '1':
            returnValue(1)
        elif resp == '0':
            returnValue(0)
        else:
            print('Error: shutter position is indeterminate.')


    # SPEED
    @setting(311, 'speed', speed='i', returns='v')
    def speed(self, c, speed=None):
        """
        Set/get speed of laser shutter.
        Arguments:
            speed   (int)   : speed mode of the shutter
        Returns:
                    (int)   : speed mode of the shutter
        """
        # todo: ensure input in range
        if speed is not None:
            if speed not in (0, 1, 2, 3):
                raise Exception('Error: invalid speed. Must be one of (0, 1, 2, 3).')
            yield self.ser.acquire()
            yield self.ser.write(str(speed))
            self.ser.release()
        yield self.ser.acquire()
        yield self.ser.write('R')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = float(resp.strip())
        if resp == 100:
            returnValue(0)
        elif resp == 50:
            returnValue(1)
        elif resp == 25:
            returnValue(2)
        elif resp == 12:
            returnValue(3)


    # MISC
    @setting(411, 'Temperature', returns='i')
    def temperature(self, c):
        """
        Gets the temperature of the laser shutter.
        Arguments:
                    (int)   : the temperature of the shutter.
        """
        yield self.ser.acquire()
        yield self.ser.write('T')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        returnValue(int(resp))


if __name__ == '__main__':
    from labrad import util
    util.runServer(SR475Server())