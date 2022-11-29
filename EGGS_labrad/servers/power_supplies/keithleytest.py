"""
### BEGIN NODE INFO
[info]
name = Keithley Test Server
version = 1.0.0
description = Talks to the Keithley Test Power Supply.
instancename = Keithley Test Server

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

from EGGS_labrad.servers.serial.serialdeviceserver_multi import MultipleSerialDeviceServer

TOGGLESIGNAL =  303980
MODESIGNAL =    303981
ACTUALSIGNAL =  303982
SETSIGNAL =     303983
MAXSIGNAL =     303984
# todo: max/ovp values
# todo: set polling minimum


class KeithleyTestServer(MultipleSerialDeviceServer):
    """
    Talks to the Keithley Test power supply.
    """

    name = 'Keithley Test Server'
    regKey = 'KeithleyTest Server'
    serNode = 'MongKok'
    port = 'COM19'

    timeout = WithUnit(5.0, 's')
    baudrate = 9600

    POLL_ON_STARTUP = False


    # SIGNALS
    toggle_update = Signal(TOGGLESIGNAL,    'signal: toggle update',    '(iv)')
    mode_update =   Signal(MODESIGNAL,      'signal: mode update',      '(ss)')
    actual_update = Signal(ACTUALSIGNAL,    'signal: actual update',    '(siv)')
    set_update =    Signal(SETSIGNAL,       'signal: set update',       '(siv)')
    max_update =    Signal(MAXSIGNAL,       'signal: max update',       '(siv)')


    # CHANNEL OUTPUT
    @setting(111, 'Channel Toggle', channel='i', status=['b', 'i'], returns='b')
    def channelToggle(self, c, channel, status=None):
        """
        Turn the power supply channel on/off.
        Arguments:
            channel (int)   : the channel number.
            status  (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        chString = 'SOUR:CHAN:OUTP:STAT'
        yield c['Serial Connection'].acquire()
        yield self._channelSelect(c, channel)

        # setter
        if status is not None:
            yield c['Serial Connection'].write(chString + ' {:d}\r\n'.format(status))

        # getter
        yield c['Serial Connection'].write(chString + '?\r\n')
        resp = yield c['Serial Connection'].read_line()
        c['Serial Connection'].release()
        returnValue(bool(int(resp)))

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
        chString = 'SOUR:VOLT:LEV:IMM:AMPL'
        yield c['Serial Connection'].acquire()
        yield self._channelSelect(c, channel)

        # setter
        if voltage is not None:
            # check input
            MAX_VOLTAGE = 30 if channel in (1, 2) else 5
            if (voltage < 0) or (voltage > MAX_VOLTAGE):
                raise Exception("Invalid Value. Voltage must be in [0, {:f}]V.".format(MAX_VOLTAGE))
            yield c['Serial Connection'].write(chString + ' {:f}\r\n'.format(voltage))

        # getter
        yield c['Serial Connection'].write(chString + '?\r\n')
        resp = yield c['Serial Connection'].read_line()
        c['Serial Connection'].release()
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
        chString = 'SOUR:CURR:LEV:IMM:AMPL'
        yield c['Serial Connection'].acquire()
        yield self._channelSelect(c, channel)

        # setter
        if current is not None:
            if (current < 0) or (current > 3):
                raise Exception("Invalid Value. Current must be in [0, 3]A.")
            yield c['Serial Connection'].write(chString + ' {:f}\r\n'.format(current))

        # getter
        yield c['Serial Connection'].write(chString + '?\r\n')
        resp = yield c['Serial Connection'].read_line()
        c['Serial Connection'].release()
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
        yield c['Serial Connection'].acquire()
        yield self._channelSelect(c, channel)

        # initiate a new voltage measurement
        yield c['Serial Connection'].write('MEAS:VOLT?\r\n')
        yield c['Serial Connection'].read_line()
        
        # fetch the new voltage measurement
        yield c['Serial Connection'].write('FETC:VOLT?\r\n')
        resp = yield c['Serial Connection'].read_line()
        c['Serial Connection'].release()
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
        yield c['Serial Connection'].acquire()
        yield self._channelSelect(c, channel)

        # initiate a new current measurement
        yield c['Serial Connection'].write('MEAS:CURR?\r\n')
        yield c['Serial Connection'].read_line()
        
        # fetch the new voltage measurement
        yield c['Serial Connection'].write('FETC:CURR?\r\n')
        resp = yield c['Serial Connection'].read_line()
        c['Serial Connection'].release()
        returnValue(float(resp))


    # HELPER
    @inlineCallbacks
    def _channelSelect(self, c, channel):
        # ensure channel is valid
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be one of: {}.".format((1, 2, 3)))
        # todo: ensure channel selection blocks
        yield c['Serial Connection'].write('INST:SEL CH{:d}\r\n'.format(channel))


if __name__ == '__main__':
    from labrad import util
    util.runServer(KeithleyTestServer())
