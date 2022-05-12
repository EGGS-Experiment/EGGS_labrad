import numpy as np
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

_RIGOLDS1000Z_PROBE_ATTENUATIONS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)


class RigolDS1000ZWrapper(GPIBDeviceWrapper):

    # SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')

    @inlineCallbacks
    def autoscale(self):
        yield self.write('AUT')

    # CHANNEL
    @inlineCallbacks
    def channel_info(self, channel):
        onoff = yield self.channel_toggle(channel)
        probeAtten = yield self.channel_probe(channel)
        scale = yield self.channel_scale(channel)
        offset = yield self.channel_offset(channel)
        coupling = yield self.channel_coupling(channel)
        invert = yield self.channel_invert(channel)
        returnValue((onoff, probeAtten, scale, offset, coupling, invert))

    @inlineCallbacks
    def channel_coupling(self, channel, coupling=None):
        chString = ':CHAN{:d}:COUP'.format(channel)
        if coupling is not None:
            coupling = coupling.upper()
            if coupling in ('AC', 'DC', 'GND'):
                yield self.write(chString + ' ' + coupling)
            else:
                raise Exception('Coupling must be one of: ' + str(('AC', 'DC', 'GND')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def channel_scale(self, channel, scale=None):
        chString = ':CHAN{:d}:SCAL'.format(channel)
        if scale is not None:
            if (scale > 1e-3) and (scale < 1e1):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def channel_probe(self, channel, atten=None):
        chString = ':CHAN{:d}:PROB'.format(channel)
        if atten is not None:
            if atten in _RIGOLDS1000Z_PROBE_ATTENUATIONS:
                yield self.write(chString + ' ' + str(atten))
            else:
                raise Exception('Probe attenuation must be one of: ' + str(_RIGOLDS1000Z_PROBE_ATTENUATIONS))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def channel_toggle(self, channel, state=None):
        chString = ':CHAN{:d}:DISP'.format(channel)
        if state is not None:
            yield self.write(chString + ' ' + str(int(state)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_invert(self, channel, invert=None):
        chString = ":CHAN{:d}:INV".format(channel)
        if invert is not None:
            yield self.write(chString + ' ' + str(int(invert)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_offset(self, channel, offset=None):
        # value is in volts
        chString = ":CHAN{:d}:OFFS".format(channel)
        if offset is not None:
            if (offset == 0) or ((offset > 1e-4) and (offset < 1e1)):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    # TRIGGER
    @inlineCallbacks
    def trigger_channel(self, channel=None):
        # note: target channel must be on
        chString = ':TRIG:EDG:SOUR'
        if channel is not None:
            if channel in (1, 2, 3, 4):
                yield self.write(chString + ' CHAN' + str(channel))
            else:
                raise Exception('Trigger channel must be one of: ' + str((1, 2, 3, 4)))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_slope(self, slope=None):
        chString = ':TRIG:EDG:SLOP'
        if slope is not None:
            slope = slope.upper()
            if slope in ('POS', 'NEG', 'RFAL'):
                yield self.write(chString + ' ' + slope)
            else:
                raise Exception('Slope must be one of: ' + str(('POS', 'NEG', 'RFAL')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_level(self, channel, level=None):
        chString = ':TRIG:EDG:LEV'
        if level is not None:
            chan_tmp = yield self.trigger_channel()
            vscale_tmp = yield self.channel_scale(int(chan_tmp[-1]))
            level_max = 5 * vscale_tmp
            if (level == 0) or (abs(level) <= level_max):
                yield self.write(chString + ' ' + str(level))
            else:
                raise Exception('Trigger level must be in range: ' + str((-level_max, level_max)))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def trigger_mode(self, mode=None):
        chString = ':TRIG:SWE'
        if mode is not None:
            if mode in ('AUTO', 'NORM', 'SING'):
                yield self.write(chString + ' ' + mode)
            else:
                raise Exception('Trigger mode must be one of: ' + str(('AUTO', 'NORM', 'SING')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    # HORIZONTAL
    @inlineCallbacks
    def horizontal_offset(self, offset=None):
        chString = ':TIM:OFFS'
        if offset is not None:
            if (offset == 0) or ((abs(offset) > 1e-6) and (abs(offset) < 1e0)):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Horizontal offset must be in range: ' + str('(1e-6, 1e0)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def horizontal_scale(self, scale=None):
        chString = ':TIM:SCAL'
        if scale is not None:
            if (scale > 1e-6) and (scale < 50):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Horizontal scale must be in range: ' + str('(1e-6, 50)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    # ACQUISITION
    @inlineCallbacks
    def get_trace(self, channel, points=1200):
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

    # MEASURE
    @inlineCallbacks
    def measure_start(self, c):
        # (re-)start measurement statistics
        self.write(":MEAS:STAT:RES")

    # @setting(211, count = 'i{count}', wait='v', returns='*(s{name} v{current} v{min} v{max} v{mean} v{std dev} v{count})')
    # def measure(self, count=0, wait=Value(0.5, 's')):
    #     '''
    #     returns the values from the measure function of the scope. if count >0, wait until
    #     scope has >= count stats before returning, waiting _wait_ time between calls.
    #
    #     Note that the measurement must be set manually on the scope for this to work.
    #     '''
    #     dev = self.selectedDevice(c)
    #
    #     #take all statistics
    #     yield self.write(":MEAS:STAT ON")
    #
    #     def parse(s):
    #         s = s.split(',')
    #         d = []
    #         while s:
    #             d += [[s[0]] + [float(x) for x in s[1:7]]]
    #             s = s[7:]
    #         return d
    #
    #     d = []
    #     while True:
    #         d = yield self.query(":MEAS:RES?")
    #         d = parse(d)
    #         counts = [x[-1] for x in d]
    #         if min(counts) >= count:
    #             break
    #         yield util.wakeupCall(wait['s'])
    #     returnValue(d)

    @inlineCallbacks
    def measure_amplitude(self, channel):
        # enable measurement of parameter
        yield self.write(":MEAS:ITEM VAMP,CHAN{:d}".format(channel))
        # get parameter value
        chString = ":MEAS:ITEM? VAMP,CHAN{:d}".format(channel)
        resp = yield self.query(chString)
        returnValue(float(resp))


    # HELPER
    def _parsePreamble(preamble):
        """
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
        """
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
