"""
### BEGIN NODE INFO
[info]
name = Elliptec Server
version = 1.0.0
description = Controls Elliptec (ELLx) Devices from ThorLabs.
instancename = Elliptec Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import codecs
from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

encode_hex = codecs.getencoder("hex_codec")
decode_hex = codecs.getdecoder("hex_codec")
from EGGS_labrad.servers import SerialDeviceServer, ContextServer

_ELL_EOL = '\r'
_ELL_ENCODING = 'ASCII'

_ELL_ERRORS_msg = {
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


class ElliptecServer(SerialDeviceServer, ContextServer):
    """
    Controls Elliptec devices from ThorLabs.
    """

    name =      'Elliptec Server'
    regKey =    'ElliptecServer'
    serNode =   'lahaina'
    port =      'COM4'

    timeout = WithUnit(5.0, 's')
    baudrate = 9600


    # SIGNALS
    error_update = Signal(999999, 'signal: error update', 's')
    position_update = Signal(999998, 'signal: position update', 'i')

    # INIT
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # instantiate class variable device_num
        self.device_num = 0

    '''
    STATUS
    '''
    @setting(11, 'Status', returns='s')
    def status(self, c):
        """
        Get error status of device.
        Returns:
            (str): the error message.
        """
        # query device and extract status from response
        resp = yield self._query(self.device_num, 'gs', cntx=c)
        status_response = _ELL_ERRORS_msg[resp]
        returnValue(status_response)

    @setting(21, 'Device Number', device_num='i', returns='i')
    def device_number(self, c, device_num=None):
        """
        Get/set the device number.

        Arguments:
            device_num  (int): the device number.
        Returns:
                        (int): the device number.
        """
        # setter
        if (device_num is not None) and ((device_num >= 0x0) and (device_num <= 0x0F)):
            self.device_num = device_num
        # get status
        return self.device_num


    '''
    MOTORS
    '''
    @setting(111, 'Motor Frequency Forward', motor_num='i', freq_hz='v', returns='')
    def motor_frequency_forward(self, c, motor_num, freq_hz=None):
        """
        Set the forward frequency of a motor.

        Arguments:
            motor_num   (int)   : the motor to set.
            freq_hz     (float) : the motor forward frequency to set (in Hz).
        Returns:
                        (float) : the motor forward frequency (in Hz).
        """
        # ensure motor number is valid
        if motor_num not in (1, 2):
            raise Exception("Error: invalid motor number. Must be in [1, 2].")

        # setter
        if freq_hz is not None:
            # ensure frequency is in valid range
            if (freq_hz <= 78000) or (freq_hz >= 106000):
                raise Exception("Error: Invalid motor frequency. Must be in [78, 106] kHz.")
            # convert frequency to period (in machine units) and express in hex as string
            period_msg = '{:04X}'.format(round(14740000 / freq_hz))

            # prepare device messages
            yield self._query(self.device_num, 'f{:d}'.format(motor_num), period_msg)

        # getter
        resp = yield self._query(self.device_num, 'i{:d}'.format(motor_num))
        freq_hz = 14740000. / int(resp[14: 18], 16)
        returnValue(freq_hz)

    @setting(112, 'Motor Frequency Backward', motor_num='i', freq='v', returns='')
    def motor_frequency_backward(self, c, motor_num, freq_hz):
        """
        Set the backward frequency of a motor.

        Arguments:
            motor_num   (int)   : the motor to set.
            freq_hz     (float) : the motor backward frequency to set (in Hz).
        Returns:
                        (float) : the motor backward frequency (in Hz).
        """
        # ensure motor number is valid
        if motor_num not in (1, 2):
            raise Exception("Error: invalid motor number. Must be in [1, 2].")

        # setter
        if freq_hz is not None:
            # ensure frequency is in valid range
            if (freq_hz <= 78000) or (freq_hz >= 106000):
                raise Exception("Error: Invalid motor frequency. Must be in [78, 106] kHz.")
            # convert frequency to period (in machine units) and express in hex as string
            period_msg = '{:04X}'.format(round(14740000 / freq_hz))

            # prepare device messages
            yield self._query(self.device_num, 'b{:d}'.format(motor_num), period_msg)

        # getter
        resp = yield self._query(self.device_num, 'i{:d}'.format(motor_num))
        freq_hz = 14740000. / int(resp[18: 23], 16)
        returnValue(freq_hz)

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


    '''
    MOVE
    '''
    @setting(211, 'Move Home', dir=['b', 'i'], returns='f')
    def move_home(self, c, dir=False):
        """
        Moves the elliptec device to the home position.

        Arguments:
            dir     (bool)  :   the direction to rotate.
                                True is clockwise, False is counterclockwise.
                                Default is False.
        Returns:
                    (float) :   the absolute position (in degrees).
        """
        # ensure rotation direction is valid
        if (type(dir) is int) and (dir not in (0, 1)):
            raise Exception('Error: input must be a boolean, 0, or 1.')

        # setter
        pos_pulses_str = yield self._query(self.device_num, 'ho', '{:d}'.format(dir), cntx=c)

        # convert position in pulses to degrees
        pos_pulses_int = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        pos_deg = pos_pulses_int / 262144. * 360.
        returnValue(pos_deg)

    @setting(212, 'Move Absolute', position=['i', 'f'], returns='f')
    def move_absolute(self, c, position):
        """
        Moves the elliptec device to a specified absolute position.

        Arguments:
            position    (float) : the absolute position to move to (in degrees).
        Returns:
                        (float) : the absolute position to move to (in degrees).
        """
        # ensure position is within +/- 360 degrees
        if (position < -360) or (position > 360):
            raise Exception('Error: input must be in range [-360, 360] degrees.')

        # convert position in degrees to pulses
        move_pulses_raw = round(position / 360. * 262144.).to_bytes(4, byteorder='big', signed=True)
        move_pulses_str = encode_hex(move_pulses_raw)[0]

        # setter
        pos_pulses_str = yield self._query(self.device_num, 'ho', move_pulses_str, cntx=c)

        # convert position in pulses to degrees
        pos_pulses_int = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        pos_deg = pos_pulses_int / 262144. * 360.
        returnValue(pos_deg)

    @setting(213, 'Move Relative', position=['i', 'f'], returns='f')
    def move_relative(self, c, position):
        """
        Moves the elliptec device relative to the current position.

        Arguments:
            position    (float) : the relative position to move (in degrees).
        Returns:
                        (float) : the absolute position to move to (in degrees).
        """
        # ensure position is within +/- 360 degrees
        if (position < -360) or (position > 360):
            raise Exception('Error: input must be in range [-360, 360] degrees.')

        # convert position in degrees to pulses
        move_pulses_raw = round(position / 360. * 262144.).to_bytes(4, byteorder='big', signed=True)
        move_pulses_str = encode_hex(move_pulses_raw)[0]

        # setter
        pos_pulses_str = yield self._query(self.device_num, 'mr', move_pulses_str, cntx=c)

        # convert position in pulses to degrees
        pos_pulses_int = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        pos_deg = pos_pulses_int / 262144. * 360.
        returnValue(pos_deg)

    @setting(221, 'Move Jog', dir=['b', 'i'], returns='f')
    def move_jog(self, c, dir):
        """
        Moves the motor by a "jog" - a discrete number of steps set
        by the setting "Move Jog Set".

        Arguments:
            dir     (bool)  :   the direction to rotate.
                                True is forward, False is backward.
        Returns:
                    (float) :   the absolute position (in degrees).
        """
        # ensure rotation direction is valid
        if (type(dir) is int) and (dir not in (0, 1)):
            raise Exception('Error: input must be a boolean, 0, or 1.')

        # get appropriate move command word and move
        cmd_msg = 'fw' if dir is True else 'bw'
        pos_pulses_str = yield self._query(self.device_num, cmd_msg, cntx=c)

        # convert position in pulses to degrees
        pos_pulses_int = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        pos_deg = pos_pulses_int / 262144. * 360.
        returnValue(pos_deg)

    @setting(222, 'Move Jog Steps', step_size=['i', 'f'], returns='f')
    def move_jog_steps(self, c, step_size=None):
        """
        Get/set the jog step size. When the setting "Move Jog" is called,
        the motor will move by the number of steps specified here.

        Arguments:
            step_size   (float) : the amount to move per jog (in degrees).
        Returns:
                        (float) : the amount to move per jog (in degrees).
        """
        # setter
        if step_size is not None:
            # ensure step size is within +/- 360 degrees
            if (step_size < -360) or (step_size > 360):
                raise Exception('Error: input must be in range [-360, 360] degrees.')

            # convert position in degrees to pulses
            jog_steps_raw = round(step_size / 360. * 262144.).to_bytes(4, byteorder='big', signed=True)
            jog_steps_str = encode_hex(jog_steps_raw)[0]

            # set jog step size
            yield self._query(self.device_num, 'sj', jog_steps_str, cntx=c)

        # getter
        jog_steps_str = yield self._query(self.device_num, 'gj', cntx=c)
        # convert step size in pulses to degrees
        jog_steps_int = int.from_bytes(decode_hex(jog_steps_str)[0], byteorder='big', signed=True)
        jog_steps_deg = jog_steps_int / 262144. * 360.
        returnValue(jog_steps_deg)

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


    '''
    POSITION
    '''
    @setting(311, 'Position', returns='f')
    def position(self, c):
        """
        Returns the current position of the motor.
        Returns:
            (float)   : the current position (in degrees).
        """
        # getter
        pos_pulses_str = yield self._query(self.device_num, 'gp', cntx=c)

        # convert position in pulses to degrees
        pos_pulses_int = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        pos_deg = pos_pulses_int / 262144. * 360.
        returnValue(pos_deg)

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


    # HELPERS
    @inlineCallbacks
    def _query(self, dev_num, cmd_msg, data_msg='', cntx=None):
        """
        Creates a message according to the ELL communication protocol.

        Arguments:
            dev_num     (int)   : the device number. Defaults to 0.
            cmd_msg     (str)   : the command message (bytes 2-3) to send to the device.
            data_msg    (str)   : parameters for the command.
            cntx        Context : the client context.
        Returns:
                        (str)   : the device response.
        """
        # create device message
        msg = "{dev:x}{cmd:s}{data}\r".format(
            dev=dev_num,
            cmd=cmd_msg,
            data=data_msg
        ).encode(_ELL_ENCODING)

        # write to device and read response
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse device response
        resp = resp.strip()
        resp_header, resp_msg = resp[1:3], resp[3:]
        # print('resp: {:s}'.format(resp))

        # notify other listeners if we have an error
        if (resp_header == 'GS') and (resp_msg is not '00'):
            self.notifyOtherListeners(cntx, _ELL_ERRORS_msg[resp_msg], self.error_update)
        # notify other listeners of the updated position
        elif resp_header == 'PO':
            # extract position from message
            position_mu = 0
            if resp_msg == b'00000000':
                position_mu = 0
            else:
                position_mu = int.from_bytes(decode_hex(resp_msg)[0], byteorder='big', signed=True)
            self.notifyOtherListeners(cntx, position_mu, self.position_update)

        # return response
        returnValue(resp_msg)


if __name__ == '__main__':
    from labrad import util
    util.runServer(ElliptecServer())
