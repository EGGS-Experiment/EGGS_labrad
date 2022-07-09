from numpy import log10
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
# todo: set am dc modulation correctly
# todo: ensure all modulation functions work
# todo: round amplitude to correct decimal places


class SMY01Wrapper(GPIBDeviceWrapper):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # need to store certain parameters since we can't
        # change them on the device without activating them
        self.amplitude_stored = -140
        self.mod_active = False
        self.mod_params = {'AM': 0, 'AF': 0, 'FM': 0, 'PHM': 0}


    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def toggle(self, onoff=None):
        # setter
        if onoff is True:
            yield self.write('LEV {:f} {}'.format(self.amplitude_stored, 'DBM'))
        elif onoff is False:
            yield self.write('LEV:OFF')
        # getter
        resp = yield self.query('LEV?')
        # need to specifically check LEVEL:OFF since there is no LEVEL:ON response
        if resp == 'LEVEL:OFF':
            returnValue(False)
        else:
            returnValue(True)


    # WAVEFORM
    @inlineCallbacks
    def frequency(self, freq):
        if freq:
            yield self.write('RF {:f}'.format(freq))
        resp = yield self.query('RF?')
        resp = self._parse(resp, 'RF')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl, units='DBM'):
        # setter
        if ampl is not None:
            # check if units are valid, set default to dBm
            if not units:
                units = 'DBM'
            elif units.upper() not in ['DBM', 'V']:
                raise Exception('Error: invalid units')
            elif units.upper() == 'V':
                ampl = self._VptoDBM(ampl)
                units = 'DBM'
            # check device output status
            resp = yield self.query('LEV?')
            # if output is disabled, store amplitude
            self.amplitude_stored = ampl
            if resp != 'LEVEL:OFF':
                yield self.write('LEV {:f} {}'.format(ampl, units.upper()))
        # getter
        resp = yield self.query('LEV?')
        # special case if rf is off
        if resp == 'LEVEL:OFF':
            returnValue(self.amplitude_stored)
        else:
            resp = self._parse(resp, 'LEVEL')
            returnValue(float(resp))


    # MODULATION
    @inlineCallbacks
    def mod_freq(self, freq):
        if freq:
            self.mod_params['AF'] = freq
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('AF {:f}'.format(freq))
        resp = yield self.query('AF?')
        resp = self._parse(resp, 'AF')
        returnValue(float(resp))

    @inlineCallbacks
    def mod_toggle(self, status):
        if status:
            # get stored modulation frequency
            freq = self.mod_params['AF']
            if self.mod_active is True:
                yield self.write('AF {:f}'.format(freq))
        resp = yield self.query('AF?')
        resp = resp.split('AF')[1]
        if resp == ':OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def am_toggle(self, onoff):
        # setter
        if onoff is not None:
            self.mod_active = True
            if onoff is True:
                # activate with updated parameter
                mod_freq = self.mod_params['AF']
                param = self.mod_params['AM']
                yield self.write('AF {:f}'.format(mod_freq))
                yield self.write('AM:I {}'.format(param))
            elif onoff is False:
                yield self.write('AM:OFF')
        # getter
        resp = yield self.query('AM?')
        if resp == 'AM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def am_depth(self, depth):
        if depth:
            self.mod_params['AM'] = depth
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('AM {:f}'.format(depth))
        resp = yield self.query('AM?')
        resp = self._parse(resp, 'AM:INT')
        returnValue(float(resp))

    @inlineCallbacks
    def fm_toggle(self, onoff):
        # setter
        if onoff is not None:
            self.mod_active = True
            if onoff is True:
                # activate with updated parameter
                mod_freq = self.mod_params['AF']
                param = self.mod_params['FM']
                yield self.write('AF {:f}'.format(mod_freq))
                yield self.write('FM:I {}'.format(param))
            elif onoff is False:
                yield self.write('FM:OFF')
        # getter
        resp = yield self.query('FM?')
        if resp == 'FM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def fm_dev(self, dev):
        if dev:
            self.mod_params['FM'] = dev
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('FM {:f}'.format(dev))
        resp = yield self.query('FM?')
        resp = self._parse(resp, 'FM:INT')
        returnValue(float(resp))

    @inlineCallbacks
    def pm_toggle(self, onoff):
        # setter
        if onoff is not None:
            self.mod_active = True
            if onoff is True:
                # activate with updated parameter
                mod_freq = self.mod_params['AF']
                param = self.mod_params['PHM']
                yield self.write('AF {:f}'.format(mod_freq))
                yield self.write('PHM:I {}'.format(param))
            elif onoff is False:
                yield self.write('PHM:OFF')
        # getter
        resp = yield self.query('PHM?')
        if resp == 'PHM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def pm_dev(self, dev):
        if dev:
            self.mod_params['PHM'] = dev
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('PHM {:f}'.format(dev))
        resp = yield self.query('PHM?')
        resp = self._parse(resp, 'PHM:INT')
        returnValue(float(resp))


    # FEEDBACK
    def feedback_toggle(self, onoff=None):
        # setter
        if onoff is not None:
            if onoff is True:
                yield self.write('AM:E:D')
            elif onoff is False:
                yield self.write('AM:OFF')
        # getter
        resp = yield self.query('AM?')
        if resp == 'AM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    def feedback_amplitude_depth(self, depth=None):
        if depth:
            yield self.write('AM:E:D {:f}'.format(depth))
        resp = yield self.query('AM?')
        resp = self._parse(resp, 'AM:E:D')
        returnValue(float(resp))


    # HELPER
    _VptoDBM = lambda self, volts_p: 10 * log10(volts_p ** 2 * 10)

    def _parse(self, resp, text):
        """
        Removes the command from the device response.
        If the returned parameter is not a number, then this function
            return 0 by default.
        """
        result = resp.split(text)[-1]
        result = result.strip()
        # in case device is off
        try:
            result = float(result)
        except Exception as e:
            result = 0
        return result
