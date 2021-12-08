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

from labrad.types import Value
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.polling_server import PollingServer
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

_TT74_STX_msg = b'\x02'
_TT74_ADDR_msg = b'\x80'
_TT74_READ_msg = b'\x30'
_TT74_WRITE_msg = b'\x31'
_TT74_ETX_msg = b'\x03'

_TT74_ERRORS_msg = {
    b'\x15': "Execution failed",
    b'\x32': "Unknown window",
    b'\x33': "Data type error",
    b'\x34': "Value out of range",
    b'\x35': "Window disabled",
}


class TwisTorr74Server(SerialDeviceServer, PollingServer):
    """
    Talks to the TwisTorr 74 Turbopump.
    """

    name = 'TwisTorr74 Server'
    regKey = 'TwisTorr74Server'
    serNode = 'mongkok'
    port = 'COM56'

    timeout = Value(5.0, 's')
    baudrate = 9600

    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', 'v')
    energy_update = Signal(999998, 'signal: energy update', 'v')
    rpm_update = Signal(999997, 'signal: rpm update', 'v')
    power_update = Signal(999996, 'signal: power update', 'b')

    # STARTUP
    def initServer(self):
        super().initServer()
        # set default units
        from twisted.internet.reactor import callLater
        callLater(5, self.setUnits)

    #@inlineCallbacks
    def setUnits(self):
        print('Setting default units to mBar.')
        pass
        # msg = self._create_message(CMD_msg=b'163', DIR_msg=_TT74_WRITE_msg, DATA_msg=b'0')
        # yield self.ser.write(msg)
        # resp = yield self.ser.read(15)
        # resp = self._parse(resp)
        # print(resp)


    # TOGGLE
    @setting(111, 'toggle', onoff='b', returns='b')
    def toggle(self, c, onoff=None):
        """
        Start or stop the pump
        Args:
            onoff   (bool)  : desired pump state
        Returns:
                    (bool)  : pump state
        """
        #create and send message to device
        message = None
        if onoff is True:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=_TT74_WRITE_msg, DATA_msg=b'1')
        elif onoff is False:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=_TT74_WRITE_msg, DATA_msg=b'0')
        elif onoff is None:
            message = yield self._create_message(CMD_msg=b'000', DIR_msg=_TT74_READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read(2)
        resp = yield self._parse(resp)
        if resp == '1':
            resp = True
        elif resp == '0':
            resp = False
        # update all other devices with new device state
        if onoff is not None:
            self.power_update(resp, self.getOtherListeners(c))
        returnValue(resp)


    # PARAMETERS
    @setting(211, 'Read Pressure', returns='v')
    def pressure_read(self, c):
        """
        Get pump pressure
        Returns:
            (float): pump pressure in mbar
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg=b'224', DIR_msg=_TT74_READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read()
        resp = float(resp)
        #send signal and return value
        self.pressure_update(resp)
        returnValue(resp)

    @setting(212, 'Read Power', returns='v')
    def power_read(self, c):
        """
        Get pump power.
        Returns:
            (float): pump power in W
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg=b'202', DIR_msg=_TT74_READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read()
        resp = yield self._parse(resp)
        resp = float(resp)
        #send signal and return value
        self.power_update(resp)
        returnValue(resp)

    @setting(213, 'Read RPM', returns='v')
    def rpm_read(self, c):
        """
        Get pump speed.
        Returns:
            (float): pump speed in RPM
        """
        #create and send message to device
        message = yield self._create_message(CMD_msg=b'226', DIR_msg=_TT74_READ_msg)
        yield self.ser.write(message)
        #read and parse answer
        resp = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read(2)
        resp = yield self._parse(resp)
        resp = float(resp)
        #send signal and return value
        self.rpm_update(resp)
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for pressure readout.
        """
        # create message
        yield self.ser.write(b'\x02\x802240\x0387')
        press = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read(2)
        yield self.ser.write(b'\x02\x802020\x0383')
        power = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read(2)
        yield self.ser.write(b'\x02\x802260\x0385')
        rpm = yield self.ser.read_line(_TT74_ETX_msg)
        yield self.ser.read(2)

        # parse responses
        press = yield self._parse(press)
        power = yield self._parse(power)
        rpm = yield self._parse(rpm)

        # notify clients
        self.pressure_update(float(press))
        self.energy_update(float(power))
        self.rpm_update(float(rpm))


    # HELPER
    def _create_message(self, CMD_msg, DIR_msg, DATA_msg=b''):
        """
        Creates a message according to the Twistorr74 serial protocol
        """
        #create message as bytearray
        msg = _TT74_STX_msg + _TT74_ADDR_msg + CMD_msg + DIR_msg + DATA_msg + _TT74_ETX_msg
        msg = bytearray(msg)
        #calculate checksum
        CRC_msg = 0x00
        for byte in msg[1:]:
            CRC_msg ^= byte
        #convert checksum to hex value and add to end
        CRC_msg = hex(CRC_msg)[2:]
        msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        return bytes(msg)

    def _parse(self, ans):
        if ans == b'':
            raise Exception('No response from device')
        # remove STX, ADDR, and CRC
        ans = ans[2:]
        #check if we have CMD and DIR and remove them if so
        if len(ans) > 1:
            ans = ans[4:]
            ans = ans.decode()
        elif ans in _TT74_ERRORS_msg:
            raise Exception(_TT74_ERRORS_msg[ans])
        elif ans == b'\x06':
            ans = 'Acknowledged'
        #if none of these cases, we just return it anyways
        return ans


if __name__ == '__main__':
    from labrad import util
    util.runServer(TwisTorr74Server())