from numpy import log10
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class AgilentE4434BWrapper(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def toggle(self, status=None):
        # setter
        if status is True:
            yield self.write(':OUTP ON')
        elif status is False:
            yield self.write(':OUTP OFF')

        # getter
        resp = yield self.query(':OUTP?')
        resp = bool(resp.strip())
        returnValue(resp)


    # WAVEFORM
    @inlineCallbacks
    def frequency(self, freq):
        # setter
        if freq is not None:
            yield self.write(':FREQ {:f}'.format(freq))

        # getter
        resp = yield self.query(':FREQ?')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl, units='DBM'):
        # setter
        if ampl is not None:
            # verify correct units
            if units.upper() not in ['DBM', 'VP', 'VPP']:
                raise Exception('Error: invalid units')
            elif units.upper() == 'VP':
                ampl = self._VptoDBM(ampl)
                units = 'DBM'
            elif units.upper() == 'VPP':
                ampl = self._VptoDBM(ampl / 2.)
                units = 'DBM'

            # send device message
            yield self.write(':POW {:f} {:s}'.format(ampl, units.upper()))

        # getter
        resp = yield self.query(':POW?')
        returnValue(float(resp))

    @inlineCallbacks
    def att_hold(self, status):
        # setter
        if status is True:
            yield self.write(':POW:ATT:AUTO ON')
        elif status is False:
            yield self.write(':POW:ATT:AUTO OFF')

        # getter
        resp = yield self.query(':POW:ATT:AUTO?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def alc_toggle(self, status):
        # setter
        if status is True:
            yield self.write(':POW:ALC:STAT ON')
        elif status is False:
            yield self.write(':POW:ALC:STAT OFF')

        # getter
        resp = yield self.query(':POW:ALC:STAT?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def alc_auto_toggle(self, status):
        # setter
        if status is True:
            yield self.write(':POW:ALC:SEAR ON')
        elif status is False:
            yield self.write(':POW:ALC:SEAR OFF')

        # getter
        resp = yield self.query(':POW:ALC:SEAR?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def alc_search(self):
        yield self.write(':POW:ALC:SEAR ONCE')


    '''
    MODULATION
    '''
    # GENERAL MODULATION
    @inlineCallbacks
    def mod_frequency(self, freq):
        raise NotImplementedError

    @inlineCallbacks
    def mod_toggle(self, status):
        # setter
        if status is True:
            yield self.write(':OUTP:MOD ON')
        elif status is False:
            yield self.write(':OUTP:MOD OFF')

        # getter
        resp = yield self.query(':OUTP:MOD?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)


    # AMPLITUDE MODULATION
    @inlineCallbacks
    def am_toggle(self, status):
        # setter
        if status is True:
            yield self.write(':AM:STAT ON')
        elif status is False:
            yield self.write(':AM:STAT OFF')

        # getter
        resp = yield self.query(':AM:STAT?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def am_depth(self, depth):
        # setter
        if depth is not None:
            # ensure depth is valid
            if (depth < 0.1) or (depth > 100.):
                raise Exception("Error: AM depth must be between 0.1% and 100%")

            # send device message
            yield self.write(':AM:DEPT {:f}'.format(depth))

        # getter
        resp = yield self.query(':AM:DEPT?')
        returnValue(float(resp))

    @inlineCallbacks
    def am_frequency(self, freq):
        # setter
        if freq is not None:
            # ensure frequency is within valid range
            if (freq < 0.1) or (freq > 5e4):
                raise Exception("Error: AM frequency must be between 0.1 Hz and 50 kHz.")

            # send device message
            yield self.write(':AM:INT:FREQ {:f}'.format(freq))

        # getter
        resp = yield self.query(':AM:INT:FREQ?')
        returnValue(float(resp))


    # FREQUENCY MODULATION
    @inlineCallbacks
    def fm_toggle(self, status):
        # setter
        if status is True:
            yield self.write(':FM:STAT ON')
        elif status is False:
            yield self.write(':FM:STAT OFF')

        # getter
        resp = yield self.query(':FM:STAT?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def fm_deviation(self, dev):
        # setter
        if dev is not None:
            # ensure deviation is valid
            if (dev < 0.1) or (dev > 100.):
                raise Exception("Error: FM deviation must be between 1kHz and 20 MHz.")

            # send device message
            yield self.write(':FM:DEV {:f}'.format(dev))

        # getter
        resp = yield self.query(':FM:DEV?')
        returnValue(float(resp))

    @inlineCallbacks
    def fm_frequency(self, freq):
        # setter
        if freq is not None:
            # ensure frequency is within valid range
            if (freq < 0.1) or (freq > 5e4):
                raise Exception("Error: FM frequency must be between 0.1 Hz and 50 kHz.")

            # send device message
            yield self.write(':FM:INT:FREQ {:f}'.format(freq))

        # getter
        resp = yield self.query(':FM:INT:FREQ?')
        returnValue(float(resp))


    # PHASE MODULATION
    @inlineCallbacks
    def pm_toggle(self, status):
        # setter
        if status is True:
            yield self.write(':PM:STAT ON')
        elif status is False:
            yield self.write(':PM:STAT OFF')

        # getter
        resp = yield self.query(':PM:STAT?')
        resp = resp.strip()
        if resp == 'OFF':
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def pm_deviation(self, dev):
        # setter
        if dev is not None:
            # ensure deviation is valid
            if (dev < 0.) or (dev > 10.):
                raise Exception("Error: PM deviation must be between 0. and 20 rad.")

            # send device message
            yield self.write(':PM:DEV {:f}'.format(dev))

        # getter
        resp = yield self.query(':PM:DEV?')
        returnValue(float(resp))

    @inlineCallbacks
    def pm_frequency(self, freq):
        # setter
        if freq is not None:
            # ensure frequency is within valid range
            if (freq < 0.1) or (freq > 5e4):
                raise Exception("Error: PM frequency must be between 0.1 Hz and 50 kHz.")

            # send device message
            yield self.write(':PM:INT:FREQ {:f}'.format(freq))

        # getter
        resp = yield self.query(':PM:INT:FREQ?')
        returnValue(float(resp))


    # HELPER FUNCTIONS
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
