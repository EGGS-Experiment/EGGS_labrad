import numpy as np
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class TektronixMSO2000Wrapper(GPIBDeviceWrapper):

    # SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')
        # todo: wait until finish reset

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')

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
        #todo

    @inlineCallbacks
    def channel_coupling(self, channel, coupling=None):
        chString = 'CH{:d}:COUP'.format(channel)
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
        chString = 'CH{:d}:SCA'.format(channel)
        if scale is not None:
            if (scale > 1e-3) and (scale < 1e1):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def channel_probe(self, channel, atten=None):
        chString = 'CH{:d}:PRO:GAIN'.format(channel)
        if atten is not None:
            if atten in (0.1, 1, 10):
                yield self.write(chString + ' ' + str(1/atten))
            else:
                raise Exception('Probe attenuation must be one of: ' + str((0.1, 1, 10)))
        resp = yield self.query(chString + '?')
        returnValue(1/float(resp))

    @inlineCallbacks
    def channel_toggle(self, channel, state=None):
        chString = 'SEL:CH{:d}'.format(channel)
        if state is not None:
            yield self.write(chString + ' ' + str(int(state)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_invert(self, channel, invert=None):
        chString = 'CH{:d}:INV'.format(channel)
        if invert is not None:
            yield self.write(chString + ' ' + str(int(invert)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_offset(self, channel, offset=None):
        # value is in volts
        chString = 'CH{:d}:OFFS'.format(channel)
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
        chString = 'TRIG:A:EDGE:SOU'
        if channel is not None:
            if channel in (1, 2, 3, 4):
                yield self.write(chString + ' CH' + str(channel))
            else:
                raise Exception('Trigger channel must be one of: ' + str((1, 2, 3, 4)))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_slope(self, slope=None):
        print('yzde')
        chString = 'TRIG:A:EDGE:SLOP'
        if slope is not None:
            slope = slope.upper()
            if slope in ('RIS', 'FALL'):
                yield self.write(chString + ' ' + slope)
            else:
                raise Exception('Slope must be one of: ' + str(('RIS', 'FALL')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    # @inlineCallbacks
    # def trigger_level(self, level=None):
    #     chString = 'TRIG:A:LEV:CH'.format(channel)
    #     #chString = 'TRIG:A:LEV:CH'.format(channel)
    #     if level is not None:
    #         chan_tmp = yield self.trigger_channel()
    #         vscale_tmp = yield self.channel_scale(int(chan_tmp[-1]))
    #         level_max = 5 * vscale_tmp
    #         if (level == 0) or (abs(level) <= level_max):
    #             yield self.write(chString + ' ' + str(level))
    #         else:
    #             raise Exception('Trigger level must be in range: ' + str((-level_max, level_max)))
    #     resp = yield self.query(chString + '?')
    #     returnValue(float(resp))
    #     #todo

    @inlineCallbacks
    def trigger_mode(self, mode=None):
        chString = 'TRIG:A:MOD'
        if mode is not None:
            if mode in ('AUTO', 'NORM'):
                yield self.write(chString + ' ' + mode)
            else:
                raise Exception('Trigger mode must be one of: ' + str(('AUTO', 'NORM')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())


    # HORIZONTAL
    @inlineCallbacks
    def horizontal_offset(self, offset=None):
        chString = 'HOR:DEL:TIM'
        if offset is not None:
            if (offset == 0) or ((abs(offset) > 1e-6) and (abs(offset) < 1e0)):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Horizontal offset must be in range: ' + str('(1e-6, 1e0)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def horizontal_scale(self, scale=None):
        chString = 'HOR:SCA'
        if scale is not None:
            if (scale > 1e-6) and (scale < 50):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Horizontal scale must be in range: ' + str('(1e-6, 50)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))


    # ACQUISITION
    @inlineCallbacks
    def get_trace(self, channel):
        # set trace parameters
        yield self.write('DAT:SOUR CH%d' %channel)
        # start point position
        yield self.write('DAT:STAR 1')
        # stop point position
        yield self.write('DAT:STOP 1000')
        # set encoding
        yield self.write('DAT:ENC ASCI')
        # transfer waveform preamble
        preamble = yield self.query('WFMO?')

        # get waveform data
        data = yield self.query('CURV?')

        # parse waveform preamble
        points, xincrement, xorigin, yincrement, yorigin, yreference = self._parsePreamble(preamble)
        # parse data
        trace = self._parseByteData(data)

        # convert data to volts
        xAxis = (np.arange(points) * xincrement + xorigin)
        yAxis = ((trace - yorigin) * yincrement + yreference)
        returnValue((xAxis, yAxis))


    # MEASURE
    @inlineCallbacks
    def measure_start(self, c):
        # (re-)start measurement statistics
        self.write('MEAS:STAT:RES')


    # HELPER
    def _parsePreamble(preamble):
        '''
        Check
        <preamble_block> ::= <format 16-bit NR1>,
                         <type 16-bit NR1>,
                         <points 32-bit NR1>,
                         <count 32-bit NR1>,
                         <xorigin 64-bit floating point NR3>,
                         <xreference 32-bit NR1>,
                         <yincrement 32-bit floating point NR3>,
                         <yorigin 32-bit floating point NR3>,
        '''
        fields = preamble.split(';')
        points = int(fields[6])
        xincrement, xorigin, xreference = list(map(float, fields[9: 12]))
        yincrement, yorigin, yreference = list(map(float, fields[13: 16]))
        return (points, xincrement, xorigin, yincrement, yorigin, yreference)

    def _parseByteData(data):
        """
        Parse byte data
        """
        trace = np.array(data.split(','), dtype=float)
        return trace
