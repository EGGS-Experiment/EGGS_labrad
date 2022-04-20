import numpy as np
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class Agilent33210AWrapper(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def toggle(self, onoff):
        # setter
        if onoff is True:
            yield self.write('LEV:ON')
        elif onoff is False:
            yield self.write('LEV:OFF')
        # getter
        resp = yield self.query('LEV?')
        # need to check LEVEL:OFF since there is no LEVEL:ON response
        if resp == 'LEVEL:OFF':
            returnValue(False)
        else:
            returnValue(True)


    # WAVEFORM
    @inlineCallbacks
    def function(self, shape):
        pass

    @inlineCallbacks
    def frequency(self, freq):
        if freq:
            yield self.write('RF ' + str(freq))
        resp = yield self.query('RF?')
        resp = self._parse(resp, 'RF')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl):
        # setter
        if ampl:
            yield self.write('LEV ' + str(ampl))
        # getter
        resp = yield self.query('LEV?')
        # strip text preamble
        resp = self._parse(resp, 'LEVEL')
        # special case if rf is off
        if resp == ':OFF':
            returnValue(0)
        returnValue(float(resp))
