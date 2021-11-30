"""
### BEGIN NODE INFO
[info]
name = TwisTorr74 Server
version = 1.0
description = Talks to the TwisTorr 74 Turbopump
instancename = TwisTorr74 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 5

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import time
import numpy as np

from labrad.types import Value
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

class TwisTorr74Server(SerialDeviceServer):
    """
    Talks to the TwisTorr 74 Turbopump.
    """

    name = 'TwisTorr74 Server'
    regKey = 'TwisTorr74Server'
    serNode = 'mongkok'
    port = 'COM56'

    timeout = Value(5.0, 's')
    baudrate = 9600

    STX_msg = b'\x02'
    ADDR_msg = b'\x80'
    READ_msg = b'\x30'
    WRITE_msg = b'\x31'
    ETX_msg = b'\x03'

    ERRORS_msg = {
        b'\x15': "Execution failed",
        b'\x32': "Unknown window",
        b'\x33': "Data type error",
        b'\x34': "Value out of range",
        b'\x35': "Window disabled",
    }

    onEvent = Signal(123456, 'signal: emitted signal', 'v')

    #TOGGLE
    @setting(111, 'toggle', onoff='b', returns='s')
    def toggle(self, c, onoff=None):
        """
        Start or stop the pump
        Args:
            onoff   (bool)  : desired pump state
        Returns:
                    (str)   : pump state
        """
        #create and send message to device
        message = None
        if onoff is True:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=self.WRITE_msg, DATA_msg=b'1')
        elif onoff is False:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=self.WRITE_msg, DATA_msg=b'0')
        elif onoff is None:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=self.READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read(10)
        resp = yield self._parse_answer(resp)
        returnValue(resp)

    #READ PRESSURE
    @setting(211, 'Read Pressure', returns='v')
    def pressure_read(self, c):
        """
        Get pump pressure
        Returns:
            (float): pump pressure in ***
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg=b'224', DIR_msg=self.READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read(19)
        resp = yield self._parse_answer(resp)
        self.onEvent(float(resp))
        returnValue(float(resp))

    #Helper functions
    def _create_message(self, CMD_msg, DIR_msg, DATA_msg=b''):
        """
        Creates a message according to the Twistorr74 serial protocol
        """
        #create message as bytearray
        msg = self.STX_msg + self.ADDR_msg + CMD_msg + DIR_msg + DATA_msg + self.ETX_msg
        msg = bytearray(msg)
        #calculate checksum
        CRC_msg = 0x00
        for byte in msg[1:]:
            CRC_msg ^= byte
        #convert checksum to hex value and add to end
        CRC_msg = hex(CRC_msg)[2:]
        msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        #todo: streamline this last bit
        return bytes(msg)

    def _parse_answer(self, ans):
        if ans == b'':
            raise Exception('No response from device')
        # remove STX, ADDR, and CRC
        ans = ans[2:-3]
        #check if we have CMD and DIR and remove them if so
        if len(ans) > 1:
            ans = ans[4:]
            ans = ans.decode()
        elif ans in self.ERRORS_msg:
            raise Exception(self.ERRORS_msg[ans])
        elif ans == b'\x06':
            ans = 'Acknowledged'
        #if none of these cases, we just return it anyways
        return ans

if __name__ == '__main__':
    from labrad import util
    util.runServer(TwisTorr74Server())