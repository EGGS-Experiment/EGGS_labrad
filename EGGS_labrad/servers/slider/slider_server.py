"""
### BEGIN NODE INFO
[info]
name = Slider Server
version = 1.0.0
description = Controls the ELL9K Slider from ThorLabs.
instancename = Slider Server

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
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.servers import SerialDeviceServer

TERMINATOR = '\r'


class SliderServer(SerialDeviceServer):
    """
    Controls the ELL9K Slider from ThorLabs.
    """

    name = 'Slider Server'
    regKey = 'SliderServer'
    serNode = 'mongkok'
    port = None

    timeout = WithUnit(5.0, 's')
    baudrate = 9600


    # SIGNALS
    #flow_update = Signal(999999, 'signal: flow update', 'v')


    # CORE
    @setting(11, 'Device Info', returns='')
    def deviceInfo(self, c):
        """
        Get slider info.
        """
        yield self.ser.acquire()
        yield self.ser.write('C')
        self.ser.release()

    @setting(12, 'Status', returns='')
    def status(self, c):
        """
        Get slider status.
        """
        yield self.ser.acquire()
        yield self.ser.write('C')
        self.ser.release()


    # MOTOR
    # motor info
    # motor freq
    # motor current curve
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


    # MOVE
    # move home
    # home offset
    # move absolute position (steps)
    # move relative position
    # get position
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


    # SPEED
    # get/set velocity compensation (fractional value)
    # jog
    # set jog step
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


    # HELPER
    def _create_message(self, CMD_msg, DIR_msg, DATA_msg=b''):
        """
        Creates a message according to the ELL9K serial protocol.
        """
        # create message as bytearray
        msg = _TT74_STX_msg + _TT74_ADDR_msg + CMD_msg + DIR_msg + DATA_msg + _TT74_ETX_msg
        msg = bytearray(msg)
        # calculate checksum
        CRC_msg = 0x00
        for byte in msg[1:]:
            CRC_msg ^= byte
        # convert checksum to hex value and add to end
        CRC_msg = hex(CRC_msg)[2:]
        msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        return bytes(msg)

    def _parse(self, ans):
        """
        Parses the ELL9K response.
        """
        if ans == b'':
            raise Exception('No response from device')
        # remove STX and ADDR
        ans = ans[2:]
        # check if we have CMD and DIR and remove them if so
        if len(ans) > 1:
            ans = ans[4:]
            ans = ans.decode()
        elif ans in _TT74_ERRORS_msg:
            raise Exception(_TT74_ERRORS_msg[ans])
        elif ans == b'\x06':
            ans = 'Acknowledged'
        # if none of these cases, just return it anyways
        return ans


if __name__ == '__main__':
    from labrad import util
    util.runServer(SliderServer())
