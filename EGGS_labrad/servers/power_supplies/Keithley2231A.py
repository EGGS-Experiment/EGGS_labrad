from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class Keithley2231AWrapper(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self, c):
        yield self.write('*CLS')

    @inlineCallbacks
    def remote(self, c, status):
        if status == True:
            yield self.write('SYST:REM')
        else:
            yield self.write('SYST:LOC')


    # CHANNEL OUTPUT
    @inlineCallbacks
    def channelToggle(self, c, channel, status=None):
        self._channelSelect(channel)
        chString = 'SOUR:CHAN:OUTP:STAT'
        if status is not None:
            yield self.write(chString + ' ' + int(status))
        resp = yield self.query(chString + '?')
        returnValue(int(resp))

    @inlineCallbacks
    def channelMode(self, c, channel, mode=None):
        VALID_MODES = ('NORMAL', 'SERIES', 'PARALLEL', 'TRACK')
        # setter
        if mode is not None:
            # ensure mode is valid
            if mode not in VALID_MODES:
                raise Exception("Invalid Value. Modes must be one of {}.".format(VALID_MODES))
            if mode == 'NORMAL':
                yield self.write('INST:COM:OFF')
            elif mode == 'SERIES':
                yield self.write('INST:COM:SER')
            elif mode == 'PARALLEL':
                yield self.write('INST:COM:PARA')
            elif mode == 'TRACK':
                yield self.write('INST:COM:TRAC')
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
            returnValue('NORMAL')

    @inlineCallbacks
    def channelVoltage(self, c, channel, voltage=None):
        self._channelSelect(channel)
        chString = 'SOUR:VOLT:LEV:IMM:AMPL'
        # ensure voltage is within valid range
        if voltage is not None:
            MAX_VOLTAGE = 30 if channel in (1, 2) else 5
            if (voltage < 0) or (voltage > MAX_VOLTAGE):
                raise Exception("Invalid Value. Voltage must be in [0, {:f}]V.".format(MAX_VOLTAGE))
            yield self.write(chString + ' ' + voltage)
        resp = yield self.query(chString + '?')
        returnValue(int(resp))

    @inlineCallbacks
    def channelCurrent(self, c, channel, current=None):
        self._channelSelect(channel)
        chString = 'SOUR:CURR:LEV:IMM:AMPL'
        # ensure current is within valid range
        if current is not None:
            if (current < 0) or (current > 3):
                raise Exception("Invalid Value. Current must be in [0, 3]A.")
            yield self.write(chString + ' ' + current)
        resp = yield self.query(chString + '?')
        returnValue(int(resp))


    # MEASURE
    @inlineCallbacks
    def measureVoltage(self, c, channel):
        self._channelSelect(channel)
        # initiate a new voltage measurement
        resp = yield self.write('MEAS:SCAL:VOLT:DC?')
        # fetch the new voltage measurement
        resp = yield self.query('FETC:VOLT:DC')
        returnValue(int(resp))

    @inlineCallbacks
    def measureCurrent(self, c, channel):
        # initiate a new current measurement
        resp = yield self.write('MEAS:SCAL:CURR:DC?')
        # fetch the new current measurement
        resp = yield self.query('FETC:CURR:DC')
        returnValue(int(resp))


    # HELPER
    #@inlineCallbacks
    def _channelSelect(self, channel):
        # ensure channel is valid
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be one of: {}.".format((1, 2, 3)))
        # todo: ensure channel selection blocks
        self.write('INST:SEL CH{:d}'.format(channel))
