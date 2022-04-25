import numpy as np
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class RigolDSA800Wrapper(GPIBDeviceWrapper):

    # SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')


    # ATTENUATION
    @inlineCallbacks
    def preamplifier(self, status):
        if status is not None:
            yield self.write(':SENS:POW:RF:GAIN:STAT {:d}'.format(status))
        resp = yield self.query(':SENS:POW:RF:GAIN:STAT?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def attenuation(self, att):
        if att is not None:
            if (att > 0) and (att < 30):
                yield self.write(':SENS:POW:RF:ATT {:f}'.format(att))
            else:
                raise Exception('Error: RF attenuation must be in range: [0, 30].')
        resp = yield self.query(':SENS:POW:RF:ATT?')
        returnValue(float(resp))


    # FREQUENCY RANGE
    @inlineCallbacks
    def frequencyStart(self, freq):
        if freq is not None:
            if (freq > 0) and (freq < 7.5e9):
                yield self.write(':SENS:FREQ:STAR {:f}'.format(freq))
            else:
                raise Exception('Error: start frequency must be in range: [0, 7.5e9].')
        resp = yield self.query(':SENS:FREQ:STAR?')
        returnValue(float(resp))

    @inlineCallbacks
    def frequencyStop(self, freq):
        if freq is not None:
            if (freq > 0) and (freq < 7.5e9):
                yield self.write(':SENS:FREQ:STOP {:f}'.format(freq))
            else:
                raise Exception('Error: stop frequency must be in range: [0, 7.5e9].')
        resp = yield self.query(':SENS:FREQ:STOP?')
        returnValue(float(resp))

    @inlineCallbacks
    def frequencyCenter(self, freq):
        if freq is not None:
            if (freq > 0) and (freq < 7.5e9):
                yield self.write(':SENS:FREQ:CENT {:f}'.format(freq))
            else:
                raise Exception('Error: center frequency must be in range: [0, 7.5e9].')
        resp = yield self.query(':SENS:FREQ:CENT?')
        returnValue(float(resp))


    # AMPLITUDE
    @inlineCallbacks
    def amplitudeReference(self, ampl):
        if ampl is not None:
            if (ampl > -100) and (ampl < 20):
                yield self.write(':DISP:WIN:TRAC:Y:SCAL:RLEV {:f}'.format(ampl))
            else:
                raise Exception('Error: display reference value must be in range: [-100, 20].')
        resp = yield self.query(':DISP:WIN:TRAC:Y:SCAL:RLEV?')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitudeOffset(self, ampl):
        if ampl is not None:
            if (ampl > -300) and (ampl < 300):
                yield self.write(':DISP:WIN:TRAC:Y:SCAL:RLEV:OFFS {:f}'.format(ampl))
            else:
                raise Exception('Error: display offset must be in range: [-300, 300].')
        resp = yield self.query(':DISP:WIN:TRAC:Y:SCAL:RLEV:OFFS?')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitudeScale(self, factor):
        if factor is not None:
            if (factor > 0.1) and (factor < 20):
                yield self.write(':DISP:WIN:TRAC:Y:SCAL:PDIV {:f}'.format(factor))
            else:
                raise Exception('Error: display scale must be in range: [0.1, 20].')
        resp = yield self.query(':DISP:WIN:TRAC:Y:SCAL:PDIV?')
        returnValue(float(resp))


    # MARKER SETUP
    @inlineCallbacks
    def markerToggle(self, channel, status):
        if status is not None:
            yield self.write(':CALC:MARK{:d}:STAT {:d}'.format(channel, status))
        resp = yield self.query(':CALC:MARK{:d}:STAT?'.format(channel))
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def markerTrace(self, channel, trace):
        if trace is not None:
            yield self.write(':CALC:MARK{:d}:TRAC {:d}'.format(channel, trace))
        resp = yield self.query(':CALC:MARK{:d}:TRAC?'.format(channel))
        returnValue(int(resp))

    @inlineCallbacks
    def markerMode(self, channel, mode):
        modeConvert = {0: 'POS', 1: 'DELT', 2: 'BAND', 3: 'SPAN'}
        modeInvert = {val: key for key, val in modeConvert.items()}
        if mode is not None:
            mode = modeConvert[mode]
            yield self.write(':CALC:MARK{:d}:MODE {:s}'.format(channel, mode))
        resp = yield self.query(':CALC:MARK{:d}:MODE?'.format(channel))
        returnValue(modeInvert[resp])

    @inlineCallbacks
    def markerReadoutMode(self, channel, mode):
        modeConvert = {0: 'FREQ', 1: 'TIME', 2: 'ITIM', 3: 'PER'}
        modeInvert = {val: key for key, val in modeConvert.items()}
        if mode is not None:
            mode = modeConvert[mode]
            yield self.write(':CALC:MARK{:d}:X:READ {:s}'.format(channel, mode))
        resp = yield self.query(':CALC:MARK{:d}:X:READ?'.format(channel))
        returnValue(modeInvert[resp])

    @inlineCallbacks
    def markerTrack(self, channel, status):
        if status is not None:
            yield self.write(':CALC:MARK{:d}:TRAC:STAT {:d}'.format(channel, status))
        resp = yield self.query(':CALC:MARK{:d}:TRAC:STAT?'.format(channel))
        returnValue(bool(int(resp)))


    # MARKER READOUT
    @inlineCallbacks
    def markerAmplitude(self, channel):
        resp = yield self.query(':CALC:MARK{:d}:Y?'.format(channel))
        returnValue(float(resp))

    @inlineCallbacks
    def markerFrequency(self, channel, freq):
        if freq is not None:
            if (freq > 0) and (freq < 1.5e9):
                yield self.write(':CALC:MARK{:d}:X {:d}'.format(channel, freq))
            else:
                raise Exception('Error: marker frequency must be in range: [0, 1.5e9].')
        resp = yield self.query(':CALC:MARK{:d}:X?'.format(channel))
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
        returnValue(float(resp))

    @inlineCallbacks
    def bandwidthResolution(self, bw):
        if bw is not None:
            if (bw > 10) and (bw < 1e7):
                yield self.write(':SENS:BAND:VID {:f}'.format(bw))
            else:
                raise Exception('Error: video bandwidth must be in range: [10, 1e7].')
        resp = yield self.query(':SENS:BAND:VID?')
        returnValue(float(resp))


    # TRACE
    @inlineCallbacks
    @inlineCallbacks
    def getTrace(self, channel, points=1200):
        # todo: :TRAC:DATA, set format :FORM:TRAC:DATA, set endianness :FORM:BORD
        # oscilloscope must be stopped to get trace
        yield self.write(':STOP')
        # set max points
        max_points = yield self.query(':ACQ:MDEP?')
        max_points = int(max_points)
        if points > max_points:
            points = max_points
        # configure trace
        yield self.write(':WAV:SOUR CHAN{:d}'.format(channel))
        yield self.write(':WAV:MODE RAW')
        yield self.write(':WAV:FORM BYTE')
        yield self.write(':WAV:STAR 1')
        yield self.write(':WAV:STOP {:d}'.format(points))

        # transfer waveform preamble
        preamble = yield self.query(':WAV:PRE?')
        # get waveform data
        data = yield self.query(':WAV:DATA?')
        # start oscope back up
        yield self.write(':RUN')

        # parse waveform preamble
        points, xincrement, xorigin, xreference, yincrement, yorigin, yreference = yield self._parsePreamble(preamble)
        # parse data
        trace = yield self._parseByteData(data)
        # format data
        xAxis = np.arange(points) * xincrement + xorigin
        yAxis = (trace - yorigin - yreference) * yincrement
        returnValue((xAxis, yAxis))


    # HELPER
    def _parsePreamble(preamble):
        '''
        <preamble_block> = <format 16-bit NR1>,
                         <type 16-bit NR1>,
                         <points 32-bit NR1>,
                         <count 32-bit NR1>,
                         <xincrement 64-bit floating point NR3>,
                         <xorigin 64-bit floating point NR3>,
                         <xreference 32-bit NR1>,
                         <yincrement 32-bit floating point NR3>,
                         <yorigin 32-bit floating point NR3>,
                         <yreference 32-bit NR1>
        '''
        fields = preamble.split(',')
        points = int(fields[2])
        xincrement, xorigin, xreference = list(map(float, fields[4: 7]))
        yincrement, yorigin, yreference = list(map(float, fields[7: 10]))
        print(str((points, xincrement, xorigin, xreference, yincrement, yorigin, yreference)))
        return (points, xincrement, xorigin, xreference, yincrement, yorigin, yreference)

    def _parseByteData(data):
        """
        Parse byte data.
        """
        # get tmc header in #NXXXXXXXXX format
        tmc_N = int(data[1])
        tmc_length = int(data[2: 2 + tmc_N])
        print("tmc_N: " + str(tmc_N))
        print("tmc_length: " + str(tmc_length))
        return np.frombuffer(data[2 + tmc_N:], dtype=np.uint8)
