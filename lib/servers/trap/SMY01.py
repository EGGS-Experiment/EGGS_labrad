from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

class SMY01Wrapper(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    #todo: handle/clear errors
    #todo: check that we can change modulation settings without accidentally activating modulation

    @inlineCallbacks
    def toggle(self, c, onoff):
        if onoff is True:
            yield self.write('LEV:ON')
        elif onoff is False:
            yield self.write('LEV:OFF')

    # WAVEFORM
    @inlineCallbacks
    def frequency(self, c, freq):
        if freq:
            yield self.write('RF ' + str(freq))
        resp = yield float(self.query('RF?'))
        returnValue(resp)

    @inlineCallbacks
    def amplitude(self, c, ampl):
        if ampl:
            yield self.write('LEV '+ str(ampl) + 'V')
        resp = yield float(self.query('LEV?'))
        returnValue(resp)


    # MODULATION
    @inlineCallbacks
    def mod_freq(self, c, freq):
        if freq:
            yield self.write('AF ' + str(freq))
        resp = yield float(self.query('AF?'))
        returnValue(resp)

    @inlineCallbacks
    def am_toggle(self, c, onoff):
        if onoff is True:
            yield self.write('AM:I')
        elif onoff is False:
            yield self.write('AM:OFF')

    @inlineCallbacks
    def am_depth(self, c, depth):
        if depth:
            yield self.write('AM ' + str(depth))
        resp = yield float(self.query('AM?'))
        returnValue(resp)

    @inlineCallbacks
    def fm_toggle(self, c, onoff):
        if onoff is True:
            yield self.write('FM:I')
        elif onoff is False:
            yield self.write('FM:OFF')

    @inlineCallbacks
    def fm_dev(self, c, dev):
        if dev:
            yield self.write('FM ' + str(dev))
        resp = yield float(self.query('FM?'))
        returnValue(resp)

    @inlineCallbacks
    def pm_toggle(self, c, onoff):
        if onoff is True:
            yield self.write(chstring + 'PHM:I')
        elif onoff is False:
            yield self.write(chstring + 'PHM:OFF')

    @inlineCallbacks
    def pm_dev(self, c, dev):
        if dev:
            yield self.write('PHM ' + str(dev))
        resp = yield float(self.query('PHM?'))
        returnValue(resp)


