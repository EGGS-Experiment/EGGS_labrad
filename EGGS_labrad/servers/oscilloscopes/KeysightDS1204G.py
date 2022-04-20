import numpy as np
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

_KEYSIGHTDS1204G_PROBE_ATTENUATIONS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)


class KeysightDS1204GWrapper(GPIBDeviceWrapper):

    # SYSTEM
    @inlineCallbacks
    def reset(self):
        """
        Reset the oscilloscopes to factory settings.
        """
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self):
        """
        Clear device status buffers.
        """
        yield self.write('*CLS')


    # CHANNEL
    @inlineCallbacks
    def channel_info(self, channel):
        """
        Get channel information.
        Arguments:
            channel (int): channel to query
        Returns:
            Tuple of (on/off, attenuation, scale, offset, coupling, invert)
        """
        onoff = yield self.channel_toggle(channel)
        probeAtten = yield self.channel_probe(channel)
        scale = yield self.channel_scale(channel)
        offset = yield self.channel_offset(channel)
        coupling = yield self.channel_coupling(channel)
        invert = yield self.channel_invert(channel)
        returnValue((onoff, probeAtten, scale, offset, coupling, invert))

    @inlineCallbacks
    def channel_coupling(self, channel, coupling=None):
        """
        Set or query channel coupling.
        Arguments:
            channel (int): Which channel to set coupling.
            coup (str): Coupling, 'AC' or 'DC'. If None (the default) just query
                the coupling without setting it.
        Returns:
            string indicating the channel's coupling.
        """
        chString = ':CHAN{:d}:COUP'.format(channel)
        if coupling is not None:
            coupling = coupling.upper()
            if coupling in ('AC', 'DC', 'GND'):
                yield self.write(chString + ' ' + coupling)
            else:
                raise Exception('Error: Coupling must be one of: (AC, DC).')
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def channel_scale(self, channel, scale=None):
        """
        Get or set the vertical scale.
        Arguments:
            channel (int): The channel to get or set.
            scale   (float): The vertical scale (in volts/div).
        Returns:
            (float): The vertical scale (in volts/div).
        """
        chString = ':CHAN{:d}:SCAL'.format(channel)
        if scale is not None:
            if (scale > 1e-3) and (scale < 1e1):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Error: Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def channel_probe(self, channel, atten=None):
        """
        todo
        Get/set the probe attenuation factor.
        Arguments:
            channel (int): the channel to get/set
            factor (float): the probe attenuation factor
        Returns:
            (float): the probe attenuation factor
        """
        chString = ':CHAN{:d}:PROB'.format(channel)
        if atten is not None:
            if atten in _KEYSIGHTDS1204G_PROBE_ATTENUATIONS:
                yield self.write(chString + ' ' + str(atten))
            else:
                raise Exception('Error: Probe attenuation must be one of: ' + str(_KEYSIGHTDS1204G_PROBE_ATTENUATIONS))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def channel_toggle(self, channel, state=None):
        """
        Set or query channel on/off state.
        Arguments:
            channel (int): the channel to get/set
            state (bool): True->On, False->Off.
        Returns:
            (bool): The channel state.
        """
        chString = ':CHAN{:d}:DISP'.format(channel)
        if state is not None:
            yield self.write(chString + ' ' + str(int(state)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_invert(self, channel, invert=None):
        """
        Get or set channel inversion.
        Arguments:
            channel (int): the channel to get/set
            invert (bool): True->invert, False->do not invert channel.
        Returns:
            (int): 0: not inverted, 1: inverted.
        """
        chString = ":CHAN{:d}:INV".format(channel)
        if invert is not None:
            yield self.write(chString + ' ' + str(int(invert)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_offset(self, channel, offset=None):
        """
        Get or set the vertical offset.
        Arguments:
            channel (int): the channel to get/set
            offset (float): Vertical offset in units of divisions. If None,
                (the default), then we only query.
        Returns:
            (float): Vertical offset in units of divisions.
        """
        # value is in volts
        chString = ":CHAN{:d}:OFFS".format(channel)
        if offset is not None:
            if (offset > 1e-4) and (offset < 1e1):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Error: Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))


    # TRIGGER
    @inlineCallbacks
    def trigger_channel(self, channel=None):
        """
        Set or query trigger channel.
        Arguments:
            source (str): channel name
        Returns:
            (str): Trigger source.
        """
        # note: target channel must be on
        chString = ':TRIG:EDG:SOUR'
        if channel is not None:
            if channel in (1, 2, 3, 4):
                yield self.write(chString + ' CHAN' + str(channel))
            else:
                raise Exception('Error: Trigger channel must be one of: ' + str((1, 2, 3, 4)))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_slope(self, slope=None):
        """
        Set or query trigger slope.
        Arguments:
            slope (str): the slope to trigger on (e.g. rising edge)
        Returns:
            (str): the slope being triggered off
        """
        chString = ':TRIG:EDG:SLOP'
        if slope is not None:
            slope = slope.upper()
            if slope in ('POS', 'NEG', 'EITH', 'ALT'):
                yield self.write(chString + ' ' + slope)
            else:
                raise Exception('Error: Slope must be one of: ' + str(('POS', 'NEG', 'EITH', 'ALT')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_level(self, level=None):
        """
        Set or query the trigger level.
        Arguments:
            channel (int)   :  the channel to set the trigger for
            level   (float) : the trigger level (in V)
        Returns:
            (float): the trigger level (in V).
        """
        chString = ':TRIG:EDG:LEV'
        if level is not None:
            chan_tmp = yield self.trigger_channel()
            vscale_tmp = yield self.channel_scale(int(chan_tmp[-1]))
            level_max = 5 * vscale_tmp
            if (level == 0) or (abs(level) <= level_max):
                yield self.write(chString + ' ' + str(level))
            else:
                raise Exception('Error: Trigger level must be in range: ' + str((-level_max, level_max)))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def trigger_mode(self, mode=None):
        """
        Set or query the trigger mode.
        Arguments:
            mode (str): The trigger mode.
        Returns:
            (str): The trigger mode.
        """
        chString = ':TRIG:SWE'
        if mode is not None:
            if mode in ('AUTO', 'NORM'):
                yield self.write(chString + ' ' + mode)
            else:
                raise Exception('Error: Trigger mode must be one of: ' + str(('AUTO', 'NORM')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())


    # HORIZONTAL
    @inlineCallbacks
    def horizontal_offset(self, offset=None):
        """
        Set or query the horizontal offset.
        Arguments:
            offset (float): the horizontal offset (in seconds).
        Returns:
            (float): the horizontal offset in (in seconds).
        """
        chString = ':TIM:POS'
        if offset is not None:
            if (offset == 0) or ((abs(offset) > 1e-6) and (abs(offset) < 1e0)):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Error: Horizontal offset must be in range: ' + str('(1e-6, 1e0)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def horizontal_scale(self, scale=None):
        """
        Set or query the horizontal scale.
        Arguments:
            scale (float): the horizontal scale (in s/div).
        Returns:
            (float): the horizontal scale (in s/div).
        """
        chString = ':TIM:SCAL'
        if scale is not None:
            if (scale > 1e-6) and (scale < 50):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Error: Horizontal scale must be in range: ' + str('(1e-6, 50)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))


    # ACQUISITION
    @inlineCallbacks
    def get_trace(self, channel, points=None):
        """
        Get a trace for a single channel.
        Arguments:
            channel: The channel for which we want to get the trace.
        Returns:
            Tuple of ((ValueArray[s]) Time axis, (ValueArray[V]) Voltages).
        """
        # first need to stop oscilloscope to record
        yield self.write(':STOP')

        # set channel to take trace on
        yield self.write(':WAV:SOUR CHAN{:d}'.format(channel))
        # use raw mode which gives us the entire on-screen waveform with full horizontal resolution
        yield self.write(':WAV:POIN:MODE RAW')
        # return format (default byte), use ASC or WORD for better vertical resolution
        yield self.write(':WAV:FORM BYTE')

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
        xAxis = (np.arange(points) * xincrement + xorigin)
        yAxis = (trace - yorigin - yreference) * yincrement
        returnValue((xAxis, yAxis))


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
        xincrement, xorigin, xreference = float(fields[4: 7])
        yincrement, yorigin, yreference = float(fields[7: 10])
        # print(str((points, xincrement, xorigin, xreference, yincrement, yorigin, yreference)))
        return (points, xincrement, xorigin, xreference, yincrement, yorigin, yreference)

    def _parseByteData(data):
        """
        Parse byte data.
        """
        # get tmc header in #NXXXXXXXXX format
        tmc_N = int(data[1])
        tmc_length = int(data[2: 2 + tmc_N])
        #print("tmc_N: " + str(tmc_N))
        #print("tmc_length: " + str(tmc_length))
        # use this return if return format is in bytes, otherwise need to adjust
        return np.frombuffer(data[2 + tmc_N:], dtype=np.uint8)
