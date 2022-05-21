"""
### BEGIN NODE INFO
[info]
name = Slider Server
version = 1.0.0
description = Controls the ELL9 Slider from ThorLabs.
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

_ELL9_EOL = '\r'
_ELL9_ENCODING = 'ASCII'

_ELL9_ERRORS_msg = {
    '00': "OK, no error",
    '01': "Communication time out",
    '02': "Mechanical time out",
    '03': "Command error or not supported",
    '04': "Value out of range",
    '05': "Module isolated",
    '06': "Module out of isolation",
    '07': "Initializing error",
    '08': "Thermal error",
    '0A': "Sensor error",
    '0B': "Motor error",
    '0C': "Out of range",
    '0D': "Over current error"
}
# todo: move_absolute, move_relative, move_jog, and position_home don't work


class SliderServer(SerialDeviceServer):
    """
    Controls the ELL9 Slider from ThorLabs.
    """

    name = 'Slider Server'
    regKey = 'SliderServer'
    serNode = 'mongkok'
    port = 'COM6'

    timeout = WithUnit(5.0, 's')
    baudrate = 9600


    # SIGNALS
    status_update = Signal(999999, 'signal: status update', 's')
    position_update = Signal(999998, 'signal: position update', 'i')


    # CORE
    @setting(11, 'Status', returns='s')
    def status(self, c):
        """
        Get error status of device.
        Returns:
            (str): the error message.
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write('0gs\r')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = resp.strip()
        # parse status for error message
        err_msg = _ELL9_ERRORS_msg[resp[3:]]
        returnValue(err_msg)


    # MOTORS
    @setting(111, 'Motor Frequency Forward', motor_num='i', freq='v', returns='')
    def motor_frequency_forward(self, c, motor_num, freq):
        """
        Set the forward frequency of a motor.

        Arguments:
            motor_num   (int)   : the motor to set.
            freq        (float) : the forward frequency to set (in Hz).
        """
        if motor_num not in (1, 2):
            raise Exception("Error: invalid motor number. Must be one of (1, 2).")
        # convert to period in machine units
        period_mu = round(14740000 / freq)
        # prepare device messages
        cmd_msg = "f{:d}".format(motor_num)
        data_msg = "8{:03x}".format(period_mu)
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(112, 'Motor Frequency Backward', motor_num='i', freq='v', returns='')
    def motor_frequency_backward(self, c, motor_num, freq):
        """
        Set the backward frequency of a motor.

        Arguments:
            motor_num   (int)   : the motor to set.
            freq        (float) : the forward frequency to set (in Hz).
        """
        if motor_num not in (1, 2):
            raise Exception("Error: invalid motor number. Must be one of (1, 2).")
        # convert to period in machine units
        period_mu = round(14740000 / freq)
        # prepare device messages
        cmd_msg = "b{:d}".format(motor_num)
        data_msg = "8{:03x}".format(period_mu)
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(121, 'Motor Frequency Search', motor_num='i', returns='')
    def motor_frequency_search(self, c, motor_num):
        """
        Request a frequency search to find the motor's optimal
        operating frequency.

        Arguments:
            motor_num   (int)   : the motor to set.
        """
        if motor_num not in (1, 2):
            raise Exception("Error: invalid motor number. Must be one of (1, 2).")
        # prepare device messages
        cmd_msg = "s{:d}".format(motor_num)
        yield self._setter(c, cmd_msg, 'status')


    # POSITION
    @setting(211, 'Move Home', returns='')
    def move_home(self, c):
        """
        Moves the slider to the home position.
        """
        # prepare device messages
        cmd_msg = "ho"
        # note: data_msg is ignored for this type of device
        data_msg = "1"
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(212, 'Move Absolute', position='i', returns='')
    def move_absolute(self, c, position):
        """
        Moves the slider to a specified absolute position.
        Arguments:
            position    (int)   : the position to move to. Must be in [1, 4].
        """
        if position not in range(1, 5):
            raise Exception("Error: invalid position. Must be in [1, 4].")
        # prepare device messages
        cmd_msg = "ma"
        data_msg = "{:08x}".format(position)
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(213, 'Move Relative', position='i', returns='')
    def move_relative(self, c, position):
        """
        Moves the slider relative to the current position.
        Arguments:
            position    (int)   : the position to move to. Must be in [1, 4].
        """
        # todo: implement
        return

    @setting(221, 'Move Jog', dir='i', returns='')
    def move_jog(self, c, dir):
        """
        Moves the motor by a "jog" - a discrete number of steps set
        by the setting "Move Jog Set".

        Arguments:
            dir (int)   : the direction to move. 0 = backwards, 1 = forwards.
        """
        if dir == 0:
            yield self._setter(c, "bw")
        elif dir == 1:
            yield self._setter(c, "fw")
        else:
            raise Exception("Error: invalid position. Must be in [1, 4].")

    @setting(222, 'Move Jog Steps', step_size='i', returns='i')
    def move_jog_steps(self, c, step_size=None):
        """
        Get/set the jog step size. When the setting "Move Jog" is called,
        the motor will move by the number of steps specified here.

        Arguments:
            step_size   (int)   : the number of steps to move. Must be in [1, 3].
        Returns:
                        (int)   : the number of steps per jog.
        """
        # setter
        if step_size is not None:
            if step_size not in range(1, 4):
                raise Exception("Error: invalid step size. Must be in [1, 3].")
            # prepare device messages
            cmd_msg = "sj"
            data_msg = "{:08x}".format(step_size)
            yield self._setter(c, cmd_msg, data_msg=data_msg)
        # getter
        cmd_msg = "gj"
        resp = yield self._setter(c, cmd_msg)
        # convert message to int
        returnValue(resp)

    @setting(231, 'Move Velocity', velocity='i', returns='i')
    def move_velocity(self, c, velocity):
        """
        Get/set the velocity by adjusting the drive power.
        Warning: drive power less than 25% to 45% may result in stalling.

        Arguments:
            velocity    (int)   : the velocity as a percentage of max power.
                                    Must be in (0, 100].
        Returns:
                        (int)   : the velocity as a percentage of max power.
        """
        # setter
        if velocity is not None:
            if (velocity <= 0) or (velocity > 100):
                raise Exception("Error: invalid step size. Must be in (1, 100].")
            # prepare device messages
            cmd_msg = "sv"
            data_msg = "{:02x}".format(velocity)
            yield self._setter(c, cmd_msg, data_msg=data_msg)
        # getter
        cmd_msg = "gv"
        resp = yield self._setter(c, cmd_msg)
        # convert message to integer
        resp = int(resp, 16)
        returnValue(resp)


    # POSITION
    @setting(311, 'Position', returns='i')
    def position(self, c):
        """
        Returns the current position of the motor.
        Returns:
            (int)   : the current position.
        """
        # getter
        cmd_msg = "gp"
        resp = yield self._setter(c, cmd_msg)
        returnValue(resp)

    @setting(312, 'Position Home', position='i', returns='i')
    def position_home(self, c, position=None):
        """
        Get/set the home position of the motor.
        Warning: the home position is set at the factory.
            Note the current default home position before adjustment.

        Arguments:
            position    (int)   : the new home position. Must be in [1, 4].
        Returns:
                        (int)   : the home position.
        """
        # setter
        if position is not None:
            if position not in range(1, 5):
                raise Exception("Error: invalid position. Must be in [1, 4].")
            # prepare device messages
            cmd_msg = "so"
            data_msg = "{:02x}".format(position)
            yield self._setter(c, cmd_msg, data_msg=data_msg)
        # getter
        resp = yield self._setter(c, "go")
        returnValue(resp)


    # HELPER
    @inlineCallbacks
    def _setter(self, c, cmd_msg, data_msg='', dev_num=0):
        """
        Creates a message according to the ELL9 communication protocol.

        Arguments:
            cmd_msg     (str)   : the command message (bytes 2-3) to send to the device.
            data_msg    (str)   : parameters for the command.
        Keyword Args:
            dev_num     (int)   : the device number. Defaults to 0.
        """
        # convert data_msg to empty string if None
        msg = "{dev:x}{cmd:s}{data}\r".format(dev=dev_num, cmd=cmd_msg, data=data_msg)
        msg = msg.encode(_ELL9_ENCODING)
        # write to device and read response
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = resp.strip()
        # print('resp: {:s}'.format(resp))
        # parse header to handle device response correctly
        resp_header, resp_msg = resp[1:3], resp[3:]
        if resp_header == 'GS':
            err_msg = _ELL9_ERRORS_msg[resp_msg]
            self.status_update(err_msg)
            # todo: return error
            returnValue(None)
        elif resp_header == 'PO':
            resp_msg = resp_msg.encode()
            # convert response to number
            if resp_msg == b'00000000':
                position = 0
            else:
                position = int.from_bytes(resp_msg, 'big', signed=True)
            self.position_update(position)
            returnValue(position)
        else:
            returnValue(resp_msg)


if __name__ == '__main__':
    from labrad import util
    util.runServer(SliderServer())
