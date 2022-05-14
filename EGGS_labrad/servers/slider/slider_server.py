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
_ELL9K_ADDR_msg = b'\x00'

_ELL9K_ERRORS_msg = {
    b'\x01': "Communication time out",
    b'\x02': "Mechanical time out",
    b'\x03': "Command error or not supported",
    b'\x04': "Value out of range",
    b'\x07': "Initializing error",
    b'\x08': "Thermal error",
    b'\x10': "Sensor error",
    b'\x11': "Motor error",
    b'\x12': "Out of range",
    b'\x13': "Over current error"
}

_ELL9K_STATUS_msg = {
    b'\x00': "OK, no error",
    b'\x05': "Module isolated",
    b'\x06': "Module out of isolation"
}


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
    @setting(11, 'Status', returns='*s')
    def status(self, c):
        """
        Get status or raise errors.
        """
        # create and send message to device
        message = yield self._create_message(CMD_msg=b'gs')
        # query
        yield self.ser.acquire()
        yield self.ser.write(message)
        resp = yield self.ser.read_line(TERMINATOR)
        yield self.ser.read(2)
        self.ser.release()
        # parse
        resp = yield self._parse(resp)
        returnValue(resp)
    
    @setting(12, 'Motor1 Info', returns='(bbvvvvv)')
    def motor1_info(self, c):
        """
        Get motor1 parameters.
        Returns:
                (bool): the state of the loop setting
                (bool): the state of the moter
                (float): current in amp
                (float): PWM increase every ms; undefined if the value is -1
                (float): PWM decrease every ms; undefined if the value is -1
                (float): forward period in s
                (float): backward period in s
        """
        # create and send message to device
        message = yield self._create_message(CMD_msg=b'i1')
        # query
        yield self.ser.acquire()
        yield self.ser.write(message)
        resp = yield self.ser.read_line(TERMINATOR)
        yield self.ser.read(2)
        self.ser.release()
        # parse
        resp = yield self._parse(resp)
        loop = bool(int(resp[0], 16))
        motor = bool(int(resp[1], 16))
        current = int(resp[2: 6], 16) / 1866 # 1 Amp of current is equal to 1866 points
        ramp_up = int(resp[6: 10], 16) if resp[6: 10] != 'FFFF' else -1
        ramp_down = int(resp[10: 14], 16) if resp[10: 14] != 'FFFF' else -1
        forward_period = int(resp[14: 18], 16)
        backward_period = int(resp[18: 22], 16)
        returnValue((loop, motor, current, ramp_up, ramp_down, forward_period, backeward_period))
    
    # MOTOR
    @setting(211, 'Save', returns='')
    def save(self, c):
        """
        Save motor parameter.
        """
        # create and send message to device
        message = yield self._create_message(CMD_msg=b'us')
        # query
        yield self.ser.acquire()
        yield self.ser.write(message)
        resp = yield self.ser.read_line(TERMINATOR)
        yield self.ser.read(2)
        self.ser.release()
        # parse
        resp = yield self._parse(resp)
    
    @setting(212, 'Set Period', dir='i', period='i', returns='')
    def set_period(self, c, dir, period):
        """
        Set forward / backward period. Must save the new parameter.
        Arguments:
            dir (int): 0 for forward period, 1 for backward period
            period (int): new period in s
        """
        cmd = 'f1' if dir == 0 else 'b1'
        digit = len(format(period, 'x'))
        if digit == 1:
            data = '800' + format(period, 'x')
        elif digit == 2:
            data = '80' + format(period, 'x')
        elif digit == 3:
            data = '8' + format(period, 'x')
        else:
            raise ValueError("Input is out of range.")
        
        # create and send message to device
        message = yield self._create_message(CMD_msg=cmd.encode(), DATA_msg=data.encode())
        # query
        yield self.ser.acquire()
        yield self.ser.write(message)
        resp = yield self.ser.read_line(TERMINATOR)
        yield self.ser.read(2)
        self.ser.release()
        # parse
        resp = yield self._parse(resp)
    
    @setting(213, 'Reset Period', dir='i', returns='')
    def reset_period(self, c, dir):
        """
        Reset the period to factory setting.
        Arguments:
            dir (int): 0 for forward period, 1 for backward period
        """
        cmd = 'f1' if dir == 0 else 'b1'
        data = '8FFF'
        # create and send message to device
        message = yield self._create_message(CMD_msg=cmd.encode(), DATA_msg=data.encode())
        # query
        yield self.ser.acquire()
        yield self.ser.write(message)
        resp = yield self.ser.read_line(TERMINATOR)
        yield self.ser.read(2)
        self.ser.release()
        # parse
        resp = yield self._parse(resp)


    # @setting(11, 'Reset', returns='')
    # def reset(self, c):
    #     """
    #     Reset laser shutter. All values are set to default.
    #     """
    #     yield self.ser.acquire()
    #     yield self.ser.write('C')
    #     self.ser.release()

    # @setting(12, 'Standby', returns='')
    # def standby(self, c):
    #     """
    #     Turns off laser shutter. Puts shutter into indeterminate state.
    #     Reactivate shutter by doing a reset.
    #     """
    #     yield self.ser.acquire()
    #     yield self.ser.write('K')
    #     self.ser.release()

    # @setting(13, 'Errors', returns='*s')
    # def standby(self, c):
    #     """
    #     Get errors.
    #     Returns:
    #     """
    #     yield self.ser.acquire()
    #     yield self.ser.write('W')
    #     err = yield self.ser.read_line('\n')
    #     self.ser.release()
    #     # todo: finish


    # # SHUTTER
    # @setting(211, 'Shutter Set', state='b', returns='i')
    # def shutterSet(self, c, state=None):
    #     """
    #     Set shutter state exactly.
    #     Arguments:
    #         state   (bool)  : open/close state of the shutter
    #     Returns:
    #                 (bool)  : shutter state
    #     """
    #     # set state
    #     if state is not None:
    #         yield self.ser.acquire()
    #         if state:
    #             yield self.ser.write('@')
    #         else:
    #             yield self.ser.write('A')
    #         self.ser.release()
    #     # get state
    #     yield self.ser.acquire()
    #     yield self.ser.write('S')
    #     resp = yield self.ser.read_line('\n')
    #     self.ser.release()
    #     if resp == '1':
    #         returnValue(1)
    #     elif resp == '0':
    #         returnValue(0)
    #     else:
    #         print('Error: shutter position is indeterminate.')

    # @setting(212, 'Shutter Toggle', returns='b')
    # def shutterToggle(self, c):
    #     """
    #     Toggle shutter state.
    #     Returns:
    #             (bool)   : shutter state
    #     """
    #     # toggle state
    #     yield self.ser.acquire()
    #     yield self.ser.write('B')
    #     self.ser.release()
    #     # get state
    #     yield self.ser.acquire()
    #     yield self.ser.write('S')
    #     resp = yield self.ser.read_line('\n')
    #     self.ser.release()
    #     if resp == '1':
    #         returnValue(1)
    #     elif resp == '0':
    #         returnValue(0)
    #     else:
    #         print('Error: shutter position is indeterminate.')


    # # SPEED
    # @setting(311, 'speed', speed='i', returns='v')
    # def speed(self, c, speed=None):
    #     """
    #     Set/get speed of laser shutter.
    #     Arguments:
    #         speed   (int)   : speed mode of the shutter
    #     Returns:
    #                 (int)   : speed mode of the shutter
    #     """
    #     # todo: ensure input in range
    #     if speed is not None:
    #         if speed not in (0, 1, 2, 3):
    #             raise Exception('Error: invalid speed. Must be one of (0, 1, 2, 3).')
    #         yield self.ser.acquire()
    #         yield self.ser.write(str(speed))
    #         self.ser.release()
    #     yield self.ser.acquire()
    #     yield self.ser.write('R')
    #     resp = yield self.ser.read_line('\n')
    #     self.ser.release()
    #     resp = float(resp.strip())
    #     if resp == 100:
    #         returnValue(0)
    #     elif resp == 50:
    #         returnValue(1)
    #     elif resp == 25:
    #         returnValue(2)
    #     elif resp == 12:
    #         returnValue(3)


    # # MISC
    # @setting(411, 'Temperature', returns='i')
    # def temperature(self, c):
    #     """
    #     Gets the temperature of the laser shutter.
    #     Arguments:
    #                 (int)   : the temperature of the shutter.
    #     """
    #     yield self.ser.acquire()
    #     yield self.ser.write('T')
    #     resp = yield self.ser.read_line('\n')
    #     self.ser.release()
    #     returnValue(int(resp))


    # HELPER
    def _create_message(self, CMD_msg, DATA_msg=b''):
        """
        Creates a message according to the ELL9K serial protocol.
        """
        # create message
        msg = _ELL9K_ADDR_msg + CMD_msg + DATA_msg
        return msg

    def _parse(self, ans):
        """
        Parses the ELL9K response.
        """
        if ans == b'':
            raise Exception('No response from device')
        # remove ADDR and CMD
        ans = ans[3:]
        # check if we have error or status
        if len(ans) > 1:
            ans = ans.decode()
        elif ans in _ELL9K_ERRORS_msg:
            raise Exception(_ELL9K_ERRORS_msg[ans])
        elif ans in _ELL9K_STATUS_meg:
            ans = _ELL9K_STATUS_meg[ans]
        # if none of these cases, just return it anyways
        return ans


if __name__ == '__main__':
    from labrad import util
    util.runServer(SliderServer())
