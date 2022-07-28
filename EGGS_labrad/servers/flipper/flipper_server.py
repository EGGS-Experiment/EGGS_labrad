"""
### BEGIN NODE INFO
[info]
name = Flipper Server
version = 1.0.0
description = Controls the MFF101 Flipper Mount from ThorLabs.
instancename = Flipper Server

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

#
class FlipperServer(SerialDeviceServer):
    """
    Controls the MFF101 Flipper from ThorLabs.
    """

    name = 'Flipper Server'
    regKey = 'FlipperServer'
    serNode = 'mongkok'
    port = 'COM6'

    timeout = WithUnit(5.0, 's')
    baudrate = 115200


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


    # MOVE/POSITION
    @setting(111, 'Move Jog', returns='i')
    def move_home(self, c):
        """
        Moves the flipper to the home position.
        """
        # prepare device messages
        cmd_msg = "ho"
        # note: data_msg is ignored for this type of device
        data_msg = "1"
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(112, 'Move Position', position='i', returns='')
    def position(self, c, position):
        """
        Moves the flipper to a specified absolute position.
        Arguments:
            position    (int)   : the position to move to. Must be in [0, 1].
        """
        # todo: setter
        # todo: getter
        if position not in (0, 1):
            raise Exception("Error: invalid position. Must be in [0, 1].")
        # prepare device messages
        cmd_msg = "ma"
        data_msg = "{:08x}".format(position)
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(121, 'Move Time', time='i', returns='i')
    def position(self, c, time):
        """
        Moves the flipper to a specified absolute position.
        Arguments:
            position    (int)   : the position to move to. Must be in [0, 1].
        """
        # todo: setter
        # todo: getter
        if position not in (0, 1):
            raise Exception("Error: invalid position. Must be in [0, 1].")
        # prepare device messages
        cmd_msg = "ma"
        data_msg = "{:08x}".format(position)
        yield self._setter(c, cmd_msg, data_msg=data_msg)


    # PINS
    @setting(211, 'Pin Mode', pin='i', mode='s', returns='(is)')
    def pin_mode(self, c, pin, mode):
        """
        Gets/sets the pin operation mode.
        """
        # prepare device messages
        cmd_msg = "ho"
        # note: data_msg is ignored for this type of device
        data_msg = "1"
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(212, 'Pin Signal', pin='i', signal='s', returns='(is)')
    def pin_signal(self, c, pin, signal):
        """
        Gets/sets the signal for the pin to respond to (if input) or output (if output).
        """
        # prepare device messages
        cmd_msg = "ho"
        # note: data_msg is ignored for this type of device
        data_msg = "1"
        yield self._setter(c, cmd_msg, data_msg=data_msg)

    @setting(221, 'Pin Time', pin='i', time='i', returns='(ii)')
    def pin_time(self, c, pin, time):
        """
        Gets/sets the pin signal time (output only).
        """
        # prepare device messages
        cmd_msg = "ho"
        # note: data_msg is ignored for this type of device
        data_msg = "1"
        yield self._setter(c, cmd_msg, data_msg=data_msg)


    # HELPER
    @inlineCallbacks
    def _setter(self, c, cmd, param1='\x00', param2='\x00', dest='\x50', source='\x01'):
        """
        Creates a message according to the ELL9 communication protocol.

        Arguments:
            cmd_msg     (str)   : the command message (bytes 2-3) to send to the device.
            data_msg    (str)   : parameters for the command.
        Keyword Args:
            dev_num     (int)   : the device number. Defaults to 0.
        """
        # convert data_msg to empty string if None
        msg = "{cmd_1:x}{cmd_0:x}{param1:x}{param2:x}{dest:x}{source:x}".format(
            cmd_1=cmd[1], cmd_2=cmd[0], param1=param1, param2=param2, dest=dest, source=source
        )
        msg = msg.encode()
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
    util.runServer(FlipperServer())
