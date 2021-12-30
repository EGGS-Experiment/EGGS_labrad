import numpy as np
from labrad.types import Value
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

_RIGOLDS1000Z_VERT_DIVISIONS = 8.0
_RIGOLDS1000Z_HORZ_DIVISIONS = 10.0
_RIGOLDS1000Z_PROBE_ATTENUATIONS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)


class RigolDS1000ZWrapper(GPIBDeviceWrapper):


    # SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')


    # CHANNEL
    @inlineCallbacks
    def channel_info(self, channel):
        # returns a tuple of (probeAtten, termination, scale, position, bwLimit, invert, units)
        resp = yield self.query(':CHAN%d?' % channel)
        # example of resp:
        # a=':CHAN1:RANG +40.0E+00;OFFS +0.00000E+00;COUP DC;IMP ONEM;DISP 1;BWL 0;INV 0;LAB "1";UNIT VOLT;PROB +10E+00;PROB:SKEW +0.00E+00;STYP SING'
        vals = []
        # the last part contains the numbers
        for part in resp.split(';'):
            vals.append(part.split(' ')[1])
        scale = vals[0]
        position = vals[1]
        coupling = vals[2]
        termination = vals[3]
        if termination == 'ONEM':
            termination = 1e6
        else:
            termination = 50
        bwLimit = vals[5]
        invert = vals[6]
        unit = vals[8]
        probeAtten = vals[9]
        # convert strings to numerical data when appropriate
        probeAtten = Value(float(probeAtten), '')
        termination = Value(float(termination), '')
        scale = Value(float(scale), '')
        position = Value(float(position), '')
        coupling = coupling
        bwLimit = Value(float(bwLimit), '')
        invert = invert
        returnValue((probeAtten, termination, scale, position, coupling, bwLimit, invert, unit))

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
            if (scale > (1e-3)) and (scale < 1e1):
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
        returnValue(bool(resp))

    @inlineCallbacks
    def channel_invert(self, channel, invert=None):
        chString = ":CHAN:{:d}:INV".format(channel)
        if invert is not None:
            yield self.write(chString + ' ' + str(int(invert)))
        resp = yield self.query(chString + '?')
        returnValue(bool(resp))

    @inlineCallbacks
    def channel_offset(self, channel, offset=None):
        # value is in volts
        chString = ":CHAN:{:d}:OFFS".format(channel)
        if offset is not None:
            #todo: get scale and probe
            if () and (): #todo
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))


    # TRIGGER
    @inlineCallbacks
    def trigger_channel(self, channel=None):
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
    def trigger_level(self, level=None):
        chString = ':TRIG:EDG:LEV'
        if level is not None:
            #todo: get range
            if (level > ) and (level < ):
                    yield self.write(chString + ' ' + str(level))
            else:
                #todo: properly
                raise Exception('Trigger level must be in range: ' + str(('POS', 'NEG', 'RFAL')))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def trigger_mode(self, mode=None):
        chString = ':TRIG:SWE'
        if mode is not None:
            if mode in ('AUTO', 'NONE', 'SING'):
                yield self.write(chString + ' ' + mode)
            else:
                raise Exception('Trigger mode must be one of: ' + str(('AUTO', 'NONE', 'SING')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())


    # HORIZONTAL
    @inlineCallbacks
    def horiz_offset(self, offset=None):
        chString = ':TIM:OFFS'
        if offset is not None:
            #todo
            if () and ():
                yield self.write(chString + ' ' + offset)
            else:
                raise Exception('Horizontal offset must be in range: ' + str())
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def horiz_scale(self, scale=None):
        chString = ':TIM:SCAL'
        if scale is not None:
            #todo
            if () and ():
                yield self.write(chString + ' ' + scale)
            else:
                raise Exception('Horizontal scale must be in range: ' + str())
        resp = yield self.query(chString + '?')
        returnValue(float(resp))


    # ACQUISITION
    @inlineCallbacks
    def get_trace(self, channel):
        # removed start and stop: start = 'i', stop = 'i' (,start=1, stop=10000)

        # first need to stop to record
        yield self.write(':STOP')

        # set trace parameters
        yield self.write(':WAV:SOUR CHAN{:d}'.format(channel))
        # trace mode
        yield self.write(':WAV:MODE RAW')
        # return format (default byte)
        yield self.write(':WAV:FORM BYTE')
        # start point position
        yield self.write(':WAV:STAR 1')
        # stop point position
        yield self.write(':WAV:STOP 12000')

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

        # convert data to volts
        timeAxis = (np.arange(points) * xincrement + xorigin)
        traceVolts = (trace - yorigin - yreference) * yincrement
        returnValue((timeAxis, traceVolts))


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
        xincrement, xorigin, xreference = float(fields[4: 7])
        yincrement, yorigin, yreference = float(fields[7: 10])
        return (points, xincrement, xorigin, xreference, yincrement, yorigin, yreference)

    def _parseByteData(data):
        """
        Parse byte data.#todo document
        """
        # get tmc header in #NXXXXXXXXX format
        tmc_N = int(data[1])
        tmc_length = int(data[2: 2 + tmc_N])
        print("tmc_N: " + str(tmc_N))
        print("tmc_length: " + str(tmc_length))
        return np.frombuffer(data[2 + tmc_N :], dtype=np.uint8)