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
from EGGS_labrad.servers import SerialDeviceServer, PollingServer

_F70_EOL_CHAR = b'\r'
_F70_START_CHAR = b'\x24'
_F70_DELIM_CHAR = b'\x2C'

_F70_OPERATION_STATUS_MSG = ('Local Off', 'Local On', 'Remote Off', 'Remote On',
                             'Cold Head Run', 'Cold Head Pause', 'Fault Off', 'Oil Fault Off')
_F70_STATUS_BITS_MSG = ('System Power', 'Motor Temperature Alarm', 'Phase Fuse Alarm',
                   'Helium Temperature Alarm', 'Water Temperature Alarm', 'Water Flow Alarm',
                   'Oil Level Alarm', 'Pressure Alarm', 'Solenoid Power', 'Serial Write Enable')



class F70Server(SerialDeviceServer, PollingServer):
    """
    Controls the F70 Helium Compressor
    """

    name = 'F70 Server'
    regKey = 'F70Server'
    serNode = 'MongKok'
    port = None

    timeout = WithUnit(3.0, 's')
    baudrate = 9600


    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', '(ii)')
    temperature_update = Signal(999998, 'signal: temperature update', '(iiii)')


    # STATUS
    @setting(11, 'Status', returns='*s')
    def status(self, c):
        """
        Get system status.
        """
        # create message
        cmd_msg = b'STA'
        msg = yield self._create_message(cmd_msg, CRC_msg=b'3504')
        # query
        resp = yield self._query(msg)
        # convert status into binary string
        status_bits = list("{:016b}".format(int(resp)))
        # get operation status
        op_status = 'Status: ' + _F70_OPERATION_STATUS_MSG[int(''.join(resp[9: 12]), base=2)]
        # remove spare bits
        del status_bits[9: 15]
        # join into message
        status_list = [': '.join(th) for th in zip(_F70_STATUS_BITS_MSG, status_bits)]
        status_list.append(op_status)
        returnValue(status_list)

    @setting(21, 'Reset', returns='s')
    def reset(self, c):
        """
        Reset the F70 compressor.
        """
        # create message
        cmd_msg = b'RS1'
        msg = yield self._create_message(cmd_msg, CRC_msg=b'2156')
        # query
        resp = yield self._query(msg)
        returnValue(resp)


    # ON/OFF
    @setting(111, 'Toggle', status='b', returns='s')
    def toggle(self, c, status):
        """
        Toggle compressor.
        """
        # create msg
        cmd_msg = b'ON1' if status else b'OFF'
        crc_msg = b'77CF' if status else b'9188'
        msg = yield self._create_message(cmd_msg, crc_msg)
        # query
        resp = yield self._query(msg)
        returnValue(resp)

    @setting(121, 'Cold Head Pause', status='b', returns='s')
    def coldHeadPause(self, c, status):
        """
        Pause/unpause cold head.
        """
        # create msg
        cmd_msg = b'CHP' if status else b'POF'
        crc_msg = b'3CCD' if status else b'07BF'
        msg = yield self._create_message(cmd_msg, crc_msg)
        # query
        resp = yield self._query(msg)
        returnValue(resp)


    # PARAMETERS
    @setting(211, 'Temperature', dev='i', returns=['i', '*i'])
    def temperature(self, c, dev=None):
        """
        Get system temperatures in Celsius.
        Returns:
            (float): temperature
        """
        # create message
        msg = None
        if dev is None:
            msg = yield self._create_message(b'TEA', CRC_msg=b'A4B9')
        elif dev in (1, 2, 3, 4):
            cmd_msg = b'TE' + bytes(str(dev), encoding='utf-8')
            crc_msg = [b'40B8', b'41F8', b'8139', b'4378'][dev - 1]
            msg = yield self._create_message(cmd_msg, crc_msg)
        else:
            raise Exception('Invalid input.')
        # query
        resp = yield self._query(msg)
        returnValue(resp)

    @setting(221, 'Pressure', dev='i', returns=['i', '*i'])
    def pressure(self, c, dev=None):
        """
        Get system pressures in psi.
        Returns:
            (float): temperature
        """
        # create message
        msg = None
        if dev is None:
            msg = yield self._create_message(b'PRA', CRC_msg=b'95F7')
        elif dev in (1, 2):
            cmd_msg = b'PR' + bytes(str(dev), encoding='utf-8')
            crc_msg = [b'71F6', b'70B6'][dev - 1]
            msg = yield self._create_message(cmd_msg, crc_msg)
        else:
            raise Exception('Invalid input.')
        # query
        resp = yield self._query(msg)
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for readout.
        """
        yield self.ser.acquire()
        self.ser.write('$TEAA4B9\r')
        respT = self.ser.read_line(_F70_EOL_CHAR)
        self.ser.write('$PRA95F7\r')
        respP = self.ser.read_line(_F70_EOL_CHAR)
        self.ser.release()
        # parse
        respT = yield self.ser._parse(respT)
        respP = yield self.ser._parse(respP)
        # todo: process
        self.temperature_update(respT)
        self.pressure_update(respP)


    # HELPER
    def _create_message(self, CMD_msg, CRC_msg=None):
        """
        Creates a message according to the F70 serial protocol.
        """
        # create message as bytearray
        msg = _F70_START_CHAR + CMD_msg
        msg = bytearray(msg)
        # calculate checksum
        if CRC_msg is None:
            CRC_msg = 0x00
            for byte in msg[1:]:
                CRC_msg ^= byte
            # convert checksum to hex value and add to end
            CRC_msg = hex(CRC_msg)[2:]
            msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        # add checksum if specified
        elif type(CRC_msg) == bytes:
            msg.extend(CRC_msg)
        elif type(CRC_msg) == str:
            msg.extend(bytearray(CRC_msg, encoding='utf-8'))
        # add EOL character
        msg.extend(_F70_EOL_CHAR)
        return bytes(msg)

    def _parse(self, ans):
        if ans == b'':
            raise Exception('No response from device')
        # remove CRC and EOL
        ans = ans.decode()
        ans = ans.split(',')[:-1]
        # check for error message otherwise remove CMD
        if ans[0] == '???':
            return 'Input Error'
        else:
            ans = ans[1:]
        # check if we have data
        if len(ans) == 0:
            return 'Acknowledged'
        elif len(ans) == 1:
            return ans[0]
        else:
            return ans

    @inlineCallbacks
    def _query(self, msg):
        # write and read
        #yield self.ser.acquire()
        #yield self.ser.write(msg)
        yield print(msg)
        #resp = yield self.ser.read_line(_F70_EOL_CHAR)
        resp = 'th1'
        #self.ser.release()
        # parse response
        #resp = yield self._parse(resp)
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(F70Server())