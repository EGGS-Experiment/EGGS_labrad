"""
### BEGIN NODE INFO
[info]
name = F70 Server
version = 1.0.0
description = Controls the F70 Helium Compressor
instancename = F70 Server

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

from EGGS_labrad.lib.servers.polling_server import PollingServer
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

_F70_EOL_CHAR = b'\r'
_F70_START_CHAR = b'\x24'
_F70_DELIM_CHAR = b'\x2C'


class F70Server(SerialDeviceServer, PollingServer):
    """
    Controls the F70 Helium Compressor
    """

    name = 'F70 Server'
    regKey = 'F70Server'
    serNode = 'MongKok'
    #port = 'COM55'

    timeout = WithUnit(3.0, 's')
    baudrate = 9600


    # STATUS
    @setting(11, 'Status', returns='s')
    def get_status(self, c):
        """
        Get controller status
        Returns:
            (str): power status of all alarms and devices
        """
        yield self.ser.acquire()
        yield self.ser.write('TS' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        returnValue(resp)


    # ON/OFF
    @setting(111, 'IP Toggle', power='b', returns='s')
    def toggle_ip(self, c, power):
        """
        Set ion pump power.
        Args:
            power   (bool)  : whether pump is to be on or off
        Returns:
                    (str)   : response from device
        """
        # setter & getter
        yield self.ser.acquire()
        if power:
            yield self.ser.write('G' + TERMINATOR)
        else:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        # parse
        if resp == _NI03_ACK_msg:
            self.ip_power_update(power, self.getOtherListeners(c))
        returnValue(resp)


    # PARAMETERS
    @setting(211, 'Temperature', dev='i', returns=['i', '*i'])
    def temperature(self, c, dev=None):
        """
        Get system temperatures.
        Returns:
            (float): temperature
        """
        if dev is None:
            dev = 'A'
        elif dev not in (1, 2, 3, 4):
            raise Exception('Invalid input.')
        # create message
        cmd_msg = 'TE' + str(dev)
        msg = yield self._create_message(cmd_msg)
        # query
        yield self.ser.acquire()
        yield self.ser.write(msg)
        resp = yield self.ser.read_line(_F70_EOL_CHAR)
        self.ser.release()
        # parse response
        resp = yield self._parse(resp)
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for readout.
        """
        # query
        yield self.ser.acquire()
        yield self.ser.write('Tb\r\n')
        ip_pressure = yield self.ser.read_line('\r')
        self.ser.release()
        # update pressure
        self.pressure_update(float(ip_pressure))


    # HELPER
    def _create_message(self, CMD_msg, DATA_msg=b''):
        """
        Creates a message according to the F70 serial protocol.
        """
        # create message as bytearray
        msg = _F70_START_CHAR + CMD_msg + DATA_msg
        msg = bytearray(msg)
        # calculate checksum
        CRC_msg = 0x00
        for byte in msg[1:]:
            CRC_msg ^= byte
        # convert checksum to hex value and add to end
        CRC_msg = hex(CRC_msg)[2:]
        msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        # add EOL character
        msg.extend(_F70_EOL_CHAR)
        return bytes(msg)

    def _parse(self, ans):
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
    util.runServer(F70Server())