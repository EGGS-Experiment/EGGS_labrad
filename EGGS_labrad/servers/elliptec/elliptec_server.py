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
# codecs necessary to convert device messages
import codecs
encode_hex = codecs.getencoder("hex_codec")
decode_hex = codecs.getdecoder("hex_codec")

from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.servers import SerialDeviceServer, ContextServer


_ELL_EOL =      '\r'
_ELL_ENCODING = 'ASCII'
# todo: migrate to enum
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
    serNode =   'mongkok'
    port =      'COM18'

    timeout =   WithUnit(5.0, 's')
    baudrate =  9600


    # SIGNALS
    error_update = Signal(999999, 'signal: error update', 's')
    position_update = Signal(999998, 'signal: position update', 'i')

    # INIT
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # instantiate class variable address number
        # used to select the hardware
        self.address_num = 0


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
        resp = yield self._query(self.address_num, 'gs', cntx=c)
        status_response = _ELL_ERRORS_msg[resp]
        returnValue(status_response)

    @setting(21, 'Address Number', address_num='i', returns='i')
    def address_number(self, c, address_num=None):
        """
        Get/set the device number for the Elliptec controller to address.
        Must be in range [0, 15].
        Arguments:
            address_num (int): the device address number.
        Returns:
                        (int): the device address number.
        """
        # setter
        # ensure device number is within range
        if (address_num is not None) and ((address_num >= 0x0) and (address_num <= 0x0F)):
            self.address_num = address_num

        # get status
        return self.address_num

    @setting(22, 'Address Information', address_num='i', returns='(isisvi)')
    def address_information(self, c, address_num=None):
        """
        Get information about the device at the given address number.

        Arguments:
            address_num (int)   :   the device address number.
        Returns:
                        (tuple) :   (device_model, serial_number,
                                    manufacture_year, firmware_version,
                                    travel_range, pulses_per_position)
        """
        # ensure device address number is valid
        addr_num = self.address_num
        if address_num is not None:
            if (address_num >= 0x0) and (address_num <= 0x0F):
                addr_num = address_num
            else:
                raise Exception("Error: invalid device address number. Must be in range [0, 15]")

        # getter
        resp = yield self._query(addr_num, 'in')

        # extract information from response
        dev_info = (
            int(resp[0: 2], 16),
            resp[2: 10],
            int(resp[10: 14]),
            resp[14: 15],
            int(resp[18: 22], 16),
            int(resp[22: 30], 16),
        )
        returnValue(dev_info)


    '''
    MOTORS
    '''
    @setting(111, 'Motor Frequency Forward', motor_num='i', freq_hz='v', returns='v')
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
            yield self._query(self.address_num, 'f{:d}'.format(motor_num), period_msg)

        # getter
        resp = yield self._query(self.address_num, 'i{:d}'.format(motor_num))
        freq_hz = 14740000. / int(resp[14: 18], 16)
        returnValue(freq_hz)

    @setting(112, 'Motor Frequency Backward', motor_num='i', freq_hz='v', returns='v')
    def motor_frequency_backward(self, c, motor_num, freq_hz=None):
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
            yield self._query(self.address_num, 'b{:d}'.format(motor_num), period_msg)

        # getter
        resp = yield self._query(self.address_num, 'i{:d}'.format(motor_num))
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
        # todo: implement
        if motor_num not in (1, 2):
            raise Exception("Error: invalid motor number. Must be one of (1, 2).")

        raise NotImplementedError


    '''
    MOVE
    '''
    @setting(211, 'Move Home', dir=['b', 'i'], returns='i')
    def move_home(self, c, dir=False):
        """
        Moves the elliptec device to the home position.

        Arguments:
            dir     (bool)  :   the direction to rotate.
                                True is clockwise, False is counterclockwise.
                                Default is False.
        Returns:
                    (int) :     the absolute position (in machine units).
        """
        # ensure movement direction is valid
        if (type(dir) is int) and (dir not in (0, 1)):
            raise Exception('Error: input must be a boolean, 0, or 1.')

        # setter
        pos_pulses_str = yield self._query(self.address_num, 'ho', '{:d}'.format(dir), cntx=c)

        # convert position in pulses to degrees
        pos_pulses_mu = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        returnValue(pos_pulses_mu)

    @setting(212, 'Move Absolute', position=['i', 'v'], returns='i')
    def move_absolute(self, c, position):
        """
        Moves the elliptec device to a specified absolute position.

        Arguments:
            position    (int) : the absolute position to move to (in machine units).
        Returns:
                        (int) : the current absolute position (in machine units).
        """
        # todo: sanitize input
        # # ensure position is within +/- 360 degrees
        # if (position < -360) or (position > 360):
        #     raise Exception('Error: input must be in range [-360, 360] degrees.')

        # convert position to hex message
        move_pulses_raw = round(position).to_bytes(4, byteorder='big', signed=True)
        move_pulses_str = encode_hex(move_pulses_raw)[0].decode()

        # setter
        pos_pulses_str = yield self._query(self.address_num, 'ma', move_pulses_str, cntx=c)

        # convert position in pulses to degrees
        pos_pulses_mu = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        returnValue(pos_pulses_mu)

    @setting(213, 'Move Relative', position=['i', 'v'], returns='i')
    def move_relative(self, c, position):
        """
        Moves the elliptec device relative to the current position.

        Arguments:
            position    (int) : the relative position to move (in degrees).
        Returns:
                        (int) : the current absolute position (in machine units).
        """
        # todo: sanitize input
        # # ensure position is within +/- 360 degrees
        # if (position < -360) or (position > 360):
        #     raise Exception('Error: input must be in range [-360, 360] degrees.')

        # convert position to hex message
        move_pulses_raw = round(position).to_bytes(4, byteorder='big', signed=True)
        move_pulses_str = encode_hex(move_pulses_raw)[0].decode()

        # setter
        pos_pulses_str = yield self._query(self.address_num, 'mr', move_pulses_str, cntx=c)

        # convert position in pulses to degrees
        pos_pulses_mu = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        returnValue(pos_pulses_mu)

    @setting(221, 'Move Jog', dir=['b', 'i'], returns='i')
    def move_jog(self, c, dir):
        """
        Moves the motor by a "jog" - a discrete number of steps set
        by the setting "Move Jog Set".

        Arguments:
            dir     (bool)  :   the direction to rotate.
                                True is forward, False is backward.
        Returns:
                    (int)   :   the current absolute position (in machine units).
        """
        # ensure rotation direction is valid
        if (type(dir) is int) and (dir not in (0, 1)):
            raise Exception('Error: input must be a boolean, 0, or 1.')

        # get appropriate move command word and move
        cmd_msg = 'fw' if bool(dir) is True else 'bw'
        pos_pulses_str = yield self._query(self.address_num, cmd_msg, cntx=c)

        # convert position in pulses to degrees
        pos_pulses_mu = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        returnValue(pos_pulses_mu)

    @setting(222, 'Move Jog Steps', step_size=['i', 'v'], returns='i')
    def move_jog_steps(self, c, step_size=None):
        """
        Get/set the jog step size. When the setting "Move Jog" is called,
        the motor will move by the number of steps specified here.

        Arguments:
            step_size   (int)   :   the amount to move per jog (in machine units).
        Returns:
                        (int)   :   the amount to move per jog (in machine units).
        """
        # setter
        if step_size is not None:
            # todo: sanitize input
            # # ensure step size is within +/- 360 degrees
            # if (step_size < -360) or (step_size > 360):
            #     raise Exception('Error: input must be in range [-360, 360] degrees.')

            # convert position in degrees to pulses
            jog_steps_raw = round(step_size).to_bytes(4, byteorder='big', signed=True)
            jog_steps_str = encode_hex(jog_steps_raw)[0].decode()

            # set jog step size
            yield self._query(self.address_num, 'sj', jog_steps_str, cntx=c)

        # getter
        jog_steps_str = yield self._query(self.address_num, 'gj', cntx=c)
        # process device response
        jog_steps_mu = int.from_bytes(decode_hex(jog_steps_str)[0], byteorder='big', signed=True)
        returnValue(jog_steps_mu)

    @setting(231, 'Move Velocity', velocity=['i', 'v'], returns='v')
    def move_velocity(self, c, velocity=None):
        """
        Get/set the velocity by adjusting the drive power.
        Warning: drive power less than 25% to 45% may result in stalling.

        Arguments:
            velocity    (int)   : the velocity as a percentage of max power.
                                    Must be in (0, 100].
        Returns:
                        (int)   : the velocity as a percentage of max power.
        """
        # todo: implement
        raise NotImplementedError
        # # setter
        # if velocity is not None:
        #     if (velocity <= 0) or (velocity > 100):
        #         raise Exception("Error: invalid step size. Must be in (1, 100].")
        #     # prepare device messages
        #     cmd_msg = "sv"
        #     data_msg = "{:02x}".format(velocity)
        #     yield self._setter(c, cmd_msg, data_msg=data_msg)
        #
        # # getter
        # cmd_msg = "gv"
        # resp = yield self._setter(c, cmd_msg)
        # # convert message to integer
        # resp = int(resp, 16)
        # returnValue(resp)


    '''
    POSITION
    '''
    @setting(311, 'Position', returns='i')
    def position(self, c):
        """
        Returns the current position of the motor.
        Returns:
            (int)   : the current absolute position (in machine units).
        """
        # getter
        pos_pulses_str = yield self._query(self.address_num, 'gp', cntx=c)

        # process device response
        pos_pulses_mu = int.from_bytes(decode_hex(pos_pulses_str)[0], byteorder='big', signed=True)
        returnValue(pos_pulses_mu)

    @setting(312, 'Position Home', position=['i','v'], returns='i')
    def position_home(self, c, position=None):
        """
        Get/set the home position of the motor.
        Warning: the home position is set at the factory.
            Note the current default home position before adjustment.

        Arguments:
            position    (int)   : the new home position. Must be in [1, 4].
        Returns:
                        (int)   : the home position (in machine units).
        """
        raise NotImplementedError
        # # setter
        # if position is not None:
        #     if position not in range(1, 5):
        #         raise Exception("Error: invalid position. Must be in [1, 4].")
        #     # prepare device messages
        #     cmd_msg = "so"
        #     data_msg = "{:02x}".format(position)
        #     yield self._setter(c, cmd_msg, data_msg=data_msg)
        #
        # # getter
        # resp = yield self._setter(c, "go")
        # returnValue(resp)


    '''
    HELPERS
    '''
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
            data=data_msg.upper()
        ).encode(_ELL_ENCODING)
        # print('\tTX: {:}'.format(msg))

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
        if (resp_header == 'GS') and (resp_msg != '00'):
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
        # print('\t\tRX: {:}'.format(resp_msg))
        returnValue(resp_msg)


if __name__ == '__main__':
    from labrad import util
    util.runServer(ElliptecServer())
