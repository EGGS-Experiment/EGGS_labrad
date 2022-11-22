"""
### BEGIN NODE INFO
[info]
name = Keithley 2231A Server
version = 1.0
description = Talks to the Keithley 2231A Power Supply.
instancename = Keithley2231AServer

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

TOGGLESIGNAL =  303980
MODESIGNAL =    303981
ACTUALSIGNAL =  303982
SETSIGNAL =     303983
MAXSIGNAL =     303984
# todo: max/ovp values
# todo: set polling minimum


class Keithley2231AServer(SerialDeviceServer, PollingServer):
    """
    Talks to the Keithley 2231A power supply.
    """

    name = 'Keithley 2231A Server'
    regKey = 'GPP3060 Server'
    serNode = 'MongKok'
    port = 'COM18'

    timeout = WithUnit(5.0, 's')
    baudrate = 115200
    bytesize = 8

    POLL_ON_STARTUP = True


    # SIGNALS
    toggle_update = Signal(TOGGLESIGNAL,    'signal: toggle update',    '(iv)')
    mode_update =   Signal(MODESIGNAL,      'signal: mode update',      '(ss)')
    actual_update = Signal(ACTUALSIGNAL,    'signal: actual update',    '(siv)')
    set_update =    Signal(SETSIGNAL,       'signal: set update',       '(siv)')
    max_update =    Signal(MAXSIGNAL,       'signal: max update',       '(siv)')


    # GENERAL
    @setting(11, "Reset", returns='')
    def reset(self):
        yield self.ser.acquire()
        yield self.ser.write('*RST')
        self.ser.release()

    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        yield self.ser.acquire()
        yield self.ser.write('*CLS')
        self.ser.release()

    @setting(21, "Remote", status=['i', 'b'], returns='')
    def remote(self, c, status):
        yield self.ser.acquire()
        if status is True:
            yield self.ser.write('SYST:REM')
        else:
            yield self.ser.write('SYST:LOC')
        self.ser.release()


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
        yield self.ser.acquire()
        yield self._channelSelect(channel)

        # setter
        if status is not None:
            yield self.ser.write(chString + ' ' + int(status))

        # getter
        yield self.ser.write(chString + '?')
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(int(resp))

    @setting(112, 'Channel Mode', channel='i', mode='s', returns='b')
    def channelMode(self, c, channel, mode=None):
        """
        Get/set the operation mode of the channel.
        # todo: allowed modes
        Arguments:
            channel (int)   : the channel number.
            mode    (str)   : the operation mode of the channel.
        Returns:
                    (str)   : the operation mode of the channel.
        """
        # todo: fix
        VALID_MODES = ('INDEPENDENT', 'SERIES', 'PARALLEL', 'TRACK')
        # setter
        if mode is not None:
            # ensure mode is valid
            if mode not in VALID_MODES:
                raise Exception("Invalid Value. Modes must be one of {}.".format(VALID_MODES))
            if mode == 'INDEPENDENT':
                yield self.ser.write('INST:COM:OFF')
            elif mode == 'SERIES':
                yield self.ser.write('INST:COM:SER')
            elif mode == 'PARALLEL':
                yield self.ser.write('INST:COM:PARA')
            elif mode == 'TRACK':
                yield self.ser.write('INST:COM:TRAC')

        # getter
        status_series = yield self.query('OUTP:SER?')
        status_parallel = yield self.query('OUTP:PARA?')
        status_track = yield self.query('OUTP:TRAC?')
        # todo: make sure returnvalue works, otherwise need normal return
        if int(status_series):
            returnValue('SERIES')
        elif int(status_parallel):
            returnValue('PARALLEL')
        elif int(status_parallel):
            returnValue('TRACK')
        else:
            returnValue('INDEPENDENT')

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
        yield self.ser.acquire()
        yield self._channelSelect(channel)

        # setter
        if voltage is not None:
            # check input
            MAX_VOLTAGE = 30 if channel in (1, 2) else 5
            if (voltage < 0) or (voltage > MAX_VOLTAGE):
                raise Exception("Invalid Value. Voltage must be in [0, {:f}]V.".format(MAX_VOLTAGE))

            yield self.ser.write(chString + ' ' + voltage)

        # getter
        yield self.ser.write(chString + '?')
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(int(resp))

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
        yield self.ser.acquire()
        yield self._channelSelect(channel)

        # setter
        if current is not None:
            if (current < 0) or (current > 3):
                raise Exception("Invalid Value. Current must be in [0, 3]A.")
            yield self.ser.write(chString + ' ' + current)

        # getter
        yield self.ser.write(chString + '?')
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(int(resp))


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
        chString = 'MEAS:SCAL:VOLT:DC?'
        yield self.ser.acquire()
        yield self._channelSelect(channel)

        # initiate a new voltage measurement
        resp = yield self.ser.write(chString)
        # fetch the new voltage measurement
        yield self.ser.write('FETC:VOLT:DC')
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(int(resp))

    @setting(212, 'Measure Current', channel='i', returns='v')
    def measureCurrent(self, c, channel):
        """
        Get the measured output current of the channel.
        Arguments:
            channel (int)   : the channel number.
        Returns:
                    (float) : the measured current (in A).
        """
        chString = 'MEAS:SCAL:CURR:DC?'
        yield self.ser.acquire()
        yield self._channelSelect(channel)

        # initiate a new current measurement
        resp = yield self.ser.write(chString)
        # fetch the new voltage measurement
        yield self.ser.write('FETC:CURR:DC')
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(int(resp))


    # HELPER
    @inlineCallbacks
    def _channelSelect(self, channel):
        # ensure channel is valid
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be one of: {}.".format((1, 2, 3)))
        # todo: ensure channel selection blocks
        yield self.ser.write('INST:SEL CH{:d}'.format(channel))
