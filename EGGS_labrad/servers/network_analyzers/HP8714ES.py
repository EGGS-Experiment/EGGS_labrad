import numpy as np
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class HP8714ESWrapper(GPIBDeviceWrapper):

    # SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')

    @inlineCallbacks
    def autoset(self):
        yield self.write(':SENS:POW:ATUN')


    # POWER
    @inlineCallbacks
    def powerToggle(self, status=None):
        if status is not None:
            yield self.write('OUTP:STAT {:d}'.format(int(status)))
        resp = yield self.query('OUTP:STAT?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def powerOutput(self, power=None):
        if power is not None:
            yield self.write('SOUR:POW {:f}'.format(power))
        resp = yield self.query('SOUR:POW?')
        returnValue(float(resp))

    @inlineCallbacks
    def powerAttenuation(self, att=None):
        raise NotImplementedError


    # SWEEP
    @inlineCallbacks
    def sweepMode(self, mode=None):
        modeConversionDict = {'FREQ': 'FIX', 'POW': 'SWE'}
        # setter
        if mode is not None:
            mode = mode.upper()
            if mode in modeConversionDict.keys():
                yield self.write('POW:MODE {}'.format(modeConversionDict[mode]))

        # getter
        resp = yield self.query('POW:MODE?')
        if int(resp) == '0':
            returnValue('FREQ')
        elif int(resp) == '1':
            returnValue('POW')

    @inlineCallbacks
    def sweepPoints(self, points=None):
        if points is not None:
            yield self.write('SENS:SWE:POIN {:d}'.format(points))
        resp = yield self.query('SENS:SWE:POIN?')
        returnValue(int(resp))


    # FREQUENCY RANGE
    @inlineCallbacks
    def frequencyStart(self, freq=None):
        if freq is not None:
            yield self.write('SENS:FREQ:STAR {:f}'.format(freq))
        resp = yield self.query('SENS:FREQ:STAR?')
        returnValue(float(resp))

    @inlineCallbacks
    def frequencyStop(self, freq=None):
        if freq is not None:
            yield self.write('SENS:FREQ:STOP {:f}'.format(freq))
        resp = yield self.query('SENS:FREQ:STOP?')
        returnValue(float(resp))

    @inlineCallbacks
    def frequencyCenter(self, freq=None):
        if freq is not None:
            yield self.write('SENS:FREQ:CENT {:f}'.format(freq))
        resp = yield self.query('SENS:FREQ:CENT?')
        returnValue(float(resp))

    @inlineCallbacks
    def frequencySpan(self, freq=None):
        if freq is not None:
            yield self.write('SENS:FREQ:SPAN {:f}'.format(freq))
        resp = yield self.query('SENS:FREQ:SPAN?')
        returnValue(float(resp))


    # AMPLITUDE
    @inlineCallbacks
    def amplitudeReference(self, ampl):
        # setter
        if ampl is not None:
            if (ampl > -100) and (ampl < 20):
                yield self.write('DISP:WIND:TRAC:Y:SCAL:RLEV {:f}'.format(ampl))
            else:
                raise Exception('Error: display reference value must be in range: [-100, 20].')
        # getter
        resp = yield self.query('DISP:WIND:TRAC:Y:SCAL:RLEV?')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitudeOffset(self, ampl):
        # setter
        if ampl is not None:
            if (ampl > -300) and (ampl < 300):
                yield self.write('DISP:WIND:TRAC:Y:SCAL:RLEV {:f}'.format(ampl))
            else:
                raise Exception('Error: display offset must be in range: [-300, 300].')
        # getter
        resp = yield self.query('DISP:WIND:TRAC:Y:SCAL:RLEV?')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitudeScale(self, factor):
        # setter
        if factor is not None:
            if (factor > 0.1) and (factor < 20):
                yield self.write('DISP:WIND:TRAC:Y:SCAL:PDIV {:f}'.format(factor))
            else:
                raise Exception('Error: display scale must be in range: [0.1, 20].')
        # getter
        resp = yield self.query('DISP:WIND:TRAC:Y:SCAL:PDIV?')
        returnValue(float(resp))


    # MARKER
    @inlineCallbacks
    def markerToggle(self, channel, status):
        if status is not None:
            yield self.write('CALC:MARK:STAT {:d}'.format(int(status)))
        resp = yield self.query('CALC:MARK:STAT?'.format(channel))
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def markerTracking(self, channel, status):
        if status is not None:
            yield self.write('CALC{:d}:MARK:FUNC:TRACK {:d}'.format(channel, status))
        resp = yield self.query('CALC{:d}:MARK:FUNC TRACK?'.format(channel))
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def markerFunction(self, channel, mode=None):
        MODECONVERT = {'MAX': 'MAX', 'MIN':'MIN', 'FREQ': 'TARG', 'BWID': 'BWID'}
        MODEINVERT = {val: key for key, val in MODECONVERT.items()}
        # setter
        if mode is not None:
            mode = mode.upper()
            if mode not in MODECONVERT.keys():
                raise Exception("Error: Invalid Mode.")
            mode = MODECONVERT[mode]
            yield self.write('CALC:MARK:FUNC:SEL {}'.format(mode))
        # getter
        resp = yield self.query('CALC:MARK:FUNC:SEL?')
        returnValue(MODEINVERT[resp])

    @inlineCallbacks
    def markerMeasure(self, channel):
        resp = yield self.query('CALC:MARK:FUNC:RES?')
        returnValue(float(resp))


    # PEAK
    @inlineCallbacks
    def peakSearch(self, status):
        if status is not None:
            yield self.write(':CALC:MARK:CPE:STAT {:d}'.format(status))
        resp = yield self.query(':CALC:MARK:CPE:STAT?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def peakSet(self, status):
        # todo:
        pass

    @inlineCallbacks
    def peakNext(self, status):
        # todo:
        pass


    # BANDWIDTH
    @inlineCallbacks
    def bandwidthSweepTime(self, time):
        if time is not None:
            if (time > 2e-6) and (time < 7500):
                yield self.write(':SENS:SWE:TIME {:f}'.format(time))
            else:
                raise Exception('Error: sweep time must be in range: [2e-6, 7500].')
        resp = yield self.query(':SENS:SWE:TIME?')
        returnValue(float(resp))

    @inlineCallbacks
    def bandwidthResolution(self, bw):
        if bw is not None:
            if (bw > 10) and (bw < 1e7):
                yield self.write(':SENS:BAND:RES {:f}'.format(bw))
            else:
                raise Exception('Error: resolution bandwidth must be in range: [10, 1e7].')
        resp = yield self.query(':SENS:BAND:RES?')
        returnValue(int(resp))


    # TRACE
    @inlineCallbacks
    def traceSetup(self, channel):
        raise NotImplementedError

    @inlineCallbacks
    def traceAcquire(self, channel):
        raise NotImplementedError
