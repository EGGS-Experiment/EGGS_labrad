from numpy import log10
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
# todo: set am dc modulation correctly
# todo: ensure all modulation functions work
# todo: round amplitude to correct decimal places

# todo: ALC

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
    def toggle(self, status=None):
        # setter
        if status is True:
            yield self.write('LEV {:f} {}'.format(self.amplitude_stored, 'DBM'))
        elif status is False:
            yield self.write('LEV:OFF')
        # getter
        resp = yield self.query('LEV?')
        # need to specifically check LEVEL:OFF since there is no LEVEL:ON response
        if resp == 'LEVEL:OFF':
            returnValue(False)
        else:
            returnValue(True)


    '''
    WAVEFORM
    '''
    # FREQUENCY
    @inlineCallbacks
    def frequency(self, freq):
        # setter
        if freq:
            yield self.write('RF {:f}'.format(freq))

        # getter
        resp = yield self.query('RF?')
        resp = self._parse(resp, 'RF')
        returnValue(float(resp))


    # AMPLITUDE
    @inlineCallbacks
    def amplitude(self, ampl, units='DBM'):
        # setter
        if ampl is not None:

            # ensure units are valid
            if units.upper() not in ['DBM', 'VP', 'VPP']:
                raise Exception('Error: invalid units')
            elif units.upper() == 'VP':
                ampl = self._VptoDBM(ampl)
                units = 'DBM'
            elif units.upper() == 'VP':
                ampl = self._VptoDBM(ampl / 2.)
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

    @inlineCallbacks
    def att_hold(self, status):
        # setter
        if status is True:
            yield self.write('AT:F')
        elif status is False:
            yield self.write('AT:N')

        # getter
        resp = yield self.query(':POW:ATT:AUTO?')
        resp = resp.strip()
        if resp == 'ATT:NOR':
            returnValue(False)
        elif resp == 'ATT:FIX':
            returnValue(True)

    @inlineCallbacks
    def alc_toggle(self, status):
        # setter
        if status is True:
            yield self.write('AL:N')
        elif status is False:
            yield self.write('AL:F')

        # getter
        resp = yield self.query('AL?')
        resp = resp.strip().split(':')[-1]
        if resp == 'FIX':
            returnValue(False)
        elif resp == 'NOR':
            returnValue(True)

    @inlineCallbacks
    def alc_auto_toggle(self, status):
        raise NotImplementedError

    @inlineCallbacks
    def alc_search(self):
        raise NotImplementedError


    '''
    MODULATION
    '''
    # GENERAL MODULATION
    @inlineCallbacks
    def mod_frequency(self, freq):
        # setter
        if freq is not None:
            self.mod_params['AF'] = freq
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('AF {:f}'.format(freq))

        # getter
        resp = yield self.query('AF?')
        resp = self._parse(resp, 'AF')
        returnValue(float(resp))

    @inlineCallbacks
    def mod_toggle(self, status):
        # setter
        if status is not None:
            # get stored modulation frequency
            freq = self.mod_params['AF']
            if self.mod_active is True:
                yield self.write('AF {:f}'.format(freq))

        # getter
        resp = yield self.query('AF?')
        resp = resp.split('AF')[1]
        if resp == ':OFF':
            returnValue(False)
        else:
            returnValue(True)


    # AMPLITUDE MODULATION
    @inlineCallbacks
    def am_toggle(self, status):
        # setter
        if status is not None:
            self.mod_active = True
            if status is True:
                # activate with updated parameter
                mod_freq = self.mod_params['AF']
                param = self.mod_params['AM']
                yield self.write('AF {:f}'.format(mod_freq))
                yield self.write('AM:I {}'.format(param))
            elif status is False:
                yield self.write('AM:OFF')

        # getter
        resp = yield self.query('AM?')
        if resp == 'AM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def am_depth(self, depth):
        # setter
        if depth is not None:
            self.mod_params['AM'] = depth
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('AM {:f}'.format(depth))

        # getter
        resp = yield self.query('AM?')
        resp = self._parse(resp, 'AM:INT')
        returnValue(float(resp))

    @inlineCallbacks
    def am_frequency(self, freq):
        raise NotImplementedError


    # FREQUENCY MODULATION
    @inlineCallbacks
    def fm_toggle(self, status):
        # setter
        if status is not None:
            self.mod_active = True
            if status is True:
                # activate with updated parameter
                mod_freq = self.mod_params['AF']
                param = self.mod_params['FM']
                yield self.write('AF {:f}'.format(mod_freq))
                yield self.write('FM:I {}'.format(param))
            elif status is False:
                yield self.write('FM:OFF')

        # getter
        resp = yield self.query('FM?')
        if resp == 'FM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def fm_deviation(self, dev):
        # setter
        if dev is not None:
            self.mod_params['FM'] = dev
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('FM {:f}'.format(dev))

        # getter
        resp = yield self.query('FM?')
        resp = self._parse(resp, 'FM:INT')
        returnValue(float(resp))

    @inlineCallbacks
    def fm_frequency(self, freq):
        raise NotImplementedError


    # PHASE MODULATION
    @inlineCallbacks
    def pm_toggle(self, status):
        # setter
        if status is not None:
            self.mod_active = True
            if status is True:
                # activate with updated parameter
                mod_freq = self.mod_params['AF']
                param = self.mod_params['PHM']
                yield self.write('AF {:f}'.format(mod_freq))
                yield self.write('PHM:I {}'.format(param))
            elif status is False:
                yield self.write('PHM:OFF')

        # getter
        resp = yield self.query('PHM?')
        if resp == 'PHM:OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def pm_deviation(self, dev):
        # setter
        if dev is not None:
            self.mod_params['PHM'] = dev
            # only write to device if modulation is already active
            if self.mod_active is True:
                yield self.write('PHM {:f}'.format(dev))

        # getter
        resp = yield self.query('PHM?')
        resp = self._parse(resp, 'PHM:INT')
        returnValue(float(resp))

    @inlineCallbacks
    def pm_frequency(self, freq):
        raise NotImplementedError


    # HELPER
    _VptoDBM = lambda self, volts_p: 10. * log10(volts_p ** 2. * 10.)

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
