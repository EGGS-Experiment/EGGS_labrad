from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class GWInstekGPP3060Wrapper(GPIBDeviceWrapper):

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
        chString = 'OUTP{:d}:STAT'.format(channel)
        # setter
        if status is not None:
            yield self.write(chString + ' ' + int(status))
        # getter
        resp = yield self.query(chString + '?')
        returnValue(int(resp))

    @inlineCallbacks
    def channelMode(self, c, channel, mode=None):
        CONVERSION_DICT = {'INDE': 'INDEPENDENT', 'SER': 'SERIES', 'PAR': 'PARALLEL',
                           'CV': 'CV', 'CC': 'CC', 'CR': 'CR'}
        # setter
        if mode is not None:
            # ensure mode is valid
            if mode not in CONVERSION_DICT.values():
                raise Exception("Invalid Value. Modes must be one of {}.".format(tuple(CONVERSION_DICT.values())))
            mode = {'INDEPENDENT': 'IND', 'SERIES': 'SER', 'PARALLEL':'PAR',
                    'CC': 'CC', 'CV': 'CV', 'CR': 'CR'}[mode]
            yield self.write('TRACK{:d}'.format(mode))
        # getter
        resp = yield self.query(':MODE{:d}?'.format(channel))
        returnValue(CONVERSION_DICT[resp])

    @inlineCallbacks
    def channelVoltage(self, c, channel, voltage=None):
        chString = 'SOUR{:d}:VOLT'.format(channel)
        # setter
        if voltage is not None:
            if (voltage < 0) or (voltage > 30):
                raise Exception("Invalid Value. Voltage must be in [0, 30]V.")
            yield self.write(chString + ' ' + voltage)
        # getter
        resp = yield self.query(chString + '?')
        returnValue(int(resp))

    @inlineCallbacks
    def channelCurrent(self, c, channel, current=None):
        chString = 'SOUR{:d}:CURR'.format(channel)
        # setter
        if current is not None:
            if (current < 0) or (current > 30):
                raise Exception("Invalid Value. Current must be in [0, 6]A.")
            yield self.write(chString + ' ' + current)
        # getter
        resp = yield self.query(chString + '?')
        returnValue(int(resp))


    # MEASURE
    @inlineCallbacks
    def measureVoltage(self, c, channel):
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be in (1, 2, 3).")
        # get the actual output voltage
        resp = yield self.query('VOUT{:d}?'.format(channel))
        returnValue(int(resp))

    @inlineCallbacks
    def measureCurrent(self, c, channel):
        if channel not in (1, 2, 3):
            raise Exception("Invalid Value. Channel must be in (1, 2, 3).")
        # get the actual output current
        resp = yield self.query('IOUT{:d}?'.format(channel))
        returnValue(int(resp))
