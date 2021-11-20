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
    def toggle(self, onoff):
        if onoff is True:
            yield self.write('LEV:ON')
        elif onoff is False:
            yield self.write('LEV:OFF')

    # WAVEFORM
    @inlineCallbacks
    def frequency(self, freq):
        if freq:
            yield self.write('RF ' + str(freq))
        resp = yield self.query('RF?')
        resp = self._parse(resp, 'RF')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl, units):
        #setter
        if ampl:
            units = units.upper()
            #check if units are valid, set default to dBm
            if not units:
                units = 'DBM'
            elif units not in ['DBM','V']:
                raise Exception('Error: invalid units')
            yield self.write('LEV '+ str(ampl) + units)
        #getter
        resp = yield self.query('LEV?')
        #strip text preamble
        resp = self._parse(resp, 'LEVEL')
        returnValue(float(resp))


    # MODULATION
    @inlineCallbacks
    def mod_freq(self, freq):
        if freq:
            yield self.write('AF ' + str(freq))
        resp = yield self.query('AF?')
        resp = self._parse(resp, 'AF')
        returnValue(resp)

    @inlineCallbacks
    def am_toggle(self, onoff):
        if onoff is True:
            yield self.write('AM:I')
        elif onoff is False:
            yield self.write('AM:OFF')

    @inlineCallbacks
    def am_depth(self, depth):
        if depth:
            yield self.write('AM ' + str(depth))
        resp = yield float(self.query('AM?'))
        returnValue(resp)

    @inlineCallbacks
    def fm_toggle(self, onoff):
        if onoff is True:
            yield self.write('FM:I')
        elif onoff is False:
            yield self.write('FM:OFF')

    @inlineCallbacks
    def fm_dev(self, dev):
        if dev:
            yield self.write('FM ' + str(dev))
        resp = yield float(self.query('FM?'))
        returnValue(resp)

    @inlineCallbacks
    def pm_toggle(self, onoff):
        if onoff is True:
            yield self.write(chstring + 'PHM:I')
        elif onoff is False:
            yield self.write(chstring + 'PHM:OFF')

    @inlineCallbacks
    def pm_dev(self, dev):
        if dev:
            yield self.write('PHM ' + str(dev))
        resp = yield float(self.query('PHM?'))
        returnValue(resp)

    #Helper functions
    _parse = lambda self, resp, text: resp.split(text)[-1]
    _dbmToV = lambda self, dbm: dbm

