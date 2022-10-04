"""
### BEGIN NODE INFO
[info]
name = Lakeshore336 Server
version = 1.0
description = Talks to the Lakeshore336 Temperature Controller
instancename = Lakeshore336 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.units import WithUnit
from labrad.server import setting, Signal, inlineCallbacks
from twisted.internet.defer import returnValue

from EGGS_labrad.servers import PollingServer, SerialDeviceServer
# todo: max values
# todo: use signals


class GPP3060Server(SerialDeviceServer, PollingServer):
    """
    Talks to the GW Instek GPP 3060 power supply.
    """

    name = 'GPP3060 Server'
    regKey = 'GPP3060 Server'
    serNode = 'MongKok'
    port = 'COM18'

    timeout = WithUnit(5.0, 's')
    baudrate = 115200
    bytesize = 8

    # SIGNALS
    # temp_update = Signal(TEMPSIGNAL, 'signal: temperature update', '(vvvv)')


    # GENERAL
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the power supply to factory settings.
        """
        yield self.ser.write('*RST\r\n')

    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        """
        Clear device status buffers.
        """
        yield self.ser.write('*CLS\r\n')

    @setting(21, "Remote", status=['i', 'b'], returns='')
    def remote(self, c, status):
        """
        Set remote mode to enable/disable remote communication.
        Arguments:
            status  (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        if status == True:
            yield self.ser.write('SYST:REM\r\n')
        else:
            yield self.ser.write('SYST:LOC\r\n')


    # CHANNEL OUTPUT
    @setting(111, 'Channel Toggle', channel='i', status=['b', 'i'], returns='b')
    def channelToggle(self, c, channel, status=None):
        """
        Turn the power supply on/off.
        Arguments:
            channel (int)   : the channel number.
            status  (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        # setter
        if status is not None:
            yield self.ser.write(':OUTP{:d}:STAT {:d}'.format(channel, status))
        # getter
        yield self.ser.write(':OUTP{:d}:STAT?\r\n'.format(channel))
        resp = yield self.ser.read_line()
        resp = resp.strip()
        if resp == 'ON':
            resp = True
        elif resp == 'OFF':
            resp = False
        returnValue(resp)

    @setting(112, 'Channel Mode', channel='i', mode='s', returns='b')
    def channelMode(self, c, channel, mode=None):
        """
        too&&&
        Arguments:
            channel (int)   : the channel number.
            mode    (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        CONVERSION_DICT = {'IND': 'INDEPENDENT', 'SER': 'SERIES', 'PAR': 'PARALLEL',
                           'CV': 'CV', 'CC': 'CC', 'CR': 'CR'}
        # setter
        if mode is not None:
            # ensure mode is valid
            if mode not in CONVERSION_DICT.values():
                raise Exception("Invalid Value. Modes must be one of {}.".format(tuple(CONVERSION_DICT.values())))
            mode = {'INDEPENDENT': 'IND', 'SERIES': 'SER', 'PARALLEL':'PAR',
                    'CC': 'CC', 'CV': 'CV', 'CR': 'CR'}[mode]
            yield self.ser.write('TRACK{:d}\r\n'.format(mode))
        # getter
        yield self.ser.write(':MODE{:d}?\r\n'.format(channel))
        resp = yield self.ser.read_line()
        returnValue(CONVERSION_DICT[resp])

    @setting(121, 'Channel Voltage', channel='i', voltage='v', returns='v')
    def channelVoltage(self, c, channel, voltage=None):
        """
        Get/set the target voltage of the power supply.
        Arguments:
            channel (int)   : the channel number.
            voltage (float) : the target voltage (in V).
        Returns:
                    (float) : the target voltage (in V).
        """
        # setter
        if voltage is not None:
            if (voltage < 0) or (voltage > 30):
                raise Exception("Invalid Value. Voltage must be in [0, 30]V.")
            yield self.ser.write('SOUR{:d}:VOLT {:f}\r\n'.format(channel, voltage))
        # getter
        yield self.ser.write('SOUR{:d}:VOLT?\r\n'.format(channel))
        resp = yield self.ser.read_line()
        returnValue(float(resp))

    @setting(122, 'Channel Current', channel='i', current='v', returns='v')
    def channelCurrent(self, c, channel, current=None):
        """
        Get/set the target current of the power supply.
        Arguments:
            channel (int)   : the channel number.
            current (float) : the target current (in A).
        Returns:
                    (float) : the target current (in A).
        """
        # setter
        if current is not None:
            if (current < 0) or (current > 30):
                raise Exception("Invalid Value. Current must be in [0, 6]A.")
            yield self.ser.write('SOUR{:d}:CURR {:f}\r\n'.format(channel, current))
        # getter
        yield self.ser.write('SOUR{:d}:CURR?\r\n'.format(channel))
        resp = yield self.ser.read_line()
        returnValue(float(resp))


    # MEASURE
    @setting(211, 'Measure Voltage', channel='i', returns='v')
    def measureVoltage(self, c, channel):
        """
        Get the measured output voltage of the channel.
        Arguments:
            channel (int)   : the channel number.
        Returns:
                    (float) : the measured voltage (in V).
        """
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be in (1, 2, 3).")
        # get the actual output voltage
        yield self.ser.write('VOUT{:d}?\r\n'.format(channel))
        resp = yield self.ser.read_line()
        resp = resp[:-1]
        returnValue(float(resp))

    @setting(212, 'Measure Current', channel='i', returns='v')
    def measureCurrent(self, c, channel):
        """
        Get the measured output current of the channel.
        Arguments:
            channel (int)   : the channel number.
        Returns:
                    (float) : the measured current (in A).
        """
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be in (1, 2, 3).")
        # get the actual output current
        yield self.ser.write('IOUT{:d}?\r\n'.format(channel))
        resp = yield self.ser.read_line()
        resp = resp[:-1]
        returnValue(float(resp))


if __name__ == '__main__':
    from labrad import util
    util.runServer(GPP3060Server())
