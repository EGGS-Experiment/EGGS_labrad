"""
### BEGIN NODE INFO
[info]
name = Oscilloscope Server
version = 1.1.0
description = Talks to oscilloscopes

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from time import sleep
from labrad.server import setting
from labrad.gpib import GPIBManagedServer

# import device wrappers
from RigolDS1000Z import RigolDS1000ZWrapper
from TektronixMSO2000 import TektronixMSO2000Wrapper
from KeysightDS1204G import KeysightDS1204GWrapper


class OscilloscopeServer(GPIBManagedServer):
    """
    Manages communication with all oscilloscopes.
    """

    name = 'Oscilloscope Server'

    deviceWrappers = {
        'RIGOL TECHNOLOGIES DS1104Z Plus': RigolDS1000ZWrapper,
        'TEKTRONIX MSO2024B': TektronixMSO2000Wrapper,
        'KEYSIGHT DS1204G': KeysightDS1204GWrapper
    }


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the oscilloscopes to factory settings.
        """
        dev = self.selectedDevice(c)
        yield dev.reset()
        sleep(5)

    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        """
        Clear device status buffers.
        """
        dev = self.selectedDevice(c)
        yield dev.clear_buffers()

    @setting(12, "Autoscale", returns='')
    def clear_buffers(self, c):
        """
        Autoscales the waveform.
        Equivalent to pressing the "AUTO" button
        on the device front panel.
        """
        dev = self.selectedDevice(c)
        yield dev.autoscale()


    # CHANNEL
    @setting(100, "Channel Info", channel='i', returns='(bvvvsb)')
    def channel_info(self, c, channel):
        """
        Get channel information.
        Arguments:
            channel (int): channel to query
        Returns:
            Tuple of (on/off, attenuation, scale, offset, coupling, invert)
        """
        return self.selectedDevice(c).channel_info(channel)

    @setting(111, "Channel Coupling", channel='i', coup='s', returns='s')
    def channel_coupling(self, c, channel, coup=None):
        """
        Set or query channel coupling.
        Arguments:
            channel (int): Which channel to set coupling.
            coup (str): Coupling, 'AC' or 'DC'. If None (the default) just query
                the coupling without setting it.
        Returns:
            string indicating the channel's coupling.
        """
        return self.selectedDevice(c).channel_coupling(channel, coup)

    @setting(112, "Channel Scale", channel='i', scale='v', returns='v')
    def channel_scale(self, c, channel, scale=None):
        """
        Get or set the vertical scale.
        Arguments:
            channel (int): The channel to get or set.
            scale   (float): The vertical scale (in volts/div).
        Returns:
            (float): The vertical scale (in volts/div).
        """
        return self.selectedDevice(c).channel_scale(channel, scale)

    @setting(113, "Channel Probe", channel='i', factor='v', returns='v')
    def channel_probe(self, c, channel, factor=None):
        """
        Get/set the probe attenuation factor.
        Arguments:
            channel (int): the channel to get/set
            factor (float): the probe attenuation factor
        Returns:
            (float): the probe attenuation factor
        """
        return self.selectedDevice(c).channel_probe(channel, factor)

    @setting(114, "Channel Toggle", channel='i', state=['i', 'b'], returns='b')
    def channel_toggle(self, c, channel, state=None):
        """
        Set or query channel on/off state.
        Arguments:
            channel (int): the channel to get/set
            state (bool): True->On, False->Off.
        Returns:
            (bool): The channel state.
        """
        return self.selectedDevice(c).channel_toggle(channel, state)

    @setting(115, "Channel Invert", channel='i', invert=['i', 'b'], returns='b')
    def channel_invert(self, c, channel, invert=None):
        """
        Get or set channel inversion.
        Arguments:
            channel (int): the channel to get/set
            invert (bool): True->invert, False->do not invert channel.
        Returns:
            (int): 0: not inverted, 1: inverted.
        """
        return self.selectedDevice(c).channel_invert(channel, invert)

    @setting(116, "Channel Offset", channel='i', offset='v', returns='v')
    def channel_offset(self, c, channel, offset=None):
        """
        Get or set the vertical offset.
        Arguments:
            channel (int): the channel to get/set
            offset (float): Vertical offset in units of divisions. If None,
                (the default), then we only query.
        Returns:
            (float): Vertical offset in units of divisions.
        """
        return self.selectedDevice(c).channel_offset(channel, offset)


    # TRIGGER
    @setting(131, "Trigger Channel", source=['s', 'i'], returns='s')
    def trigger_channel(self, c, source=None):
        """
        Set or query trigger channel.
        Arguments:
            source (str): channel name
        Returns:
            (str): Trigger source.
        """
        if source == '':
            source = None
        return self.selectedDevice(c).trigger_channel(source)

    @setting(132, "Trigger Slope", slope='s', returns='s')
    def trigger_slope(self, c, slope=None):
        """
        Set or query trigger slope.
        Arguments:
            slope (str): the slope to trigger on (e.g. rising edge)
        Returns:
            (str): the slope being triggered off
        """
        return self.selectedDevice(c).trigger_slope(slope)

    @setting(133, "Trigger Level", channel='i', level='v', returns='v')
    def trigger_level(self, c, channel, level=None):
        """
        Set or query the trigger level.
        Arguments:
            channel (int)   :  the channel to set the trigger for
            level   (float) : the trigger level (in V)
        Returns:
            (float): the trigger level (in V).
        """
        return self.selectedDevice(c).trigger_level(channel, level)

    @setting(134, "Trigger Mode", mode='s', returns='s')
    def trigger_mode(self, c, mode=None):
        """
        Set or query the trigger mode.
        Arguments:
            mode (str): The trigger mode.
        Returns:
            (str): The trigger mode.
        """
        return self.selectedDevice(c).trigger_mode(mode)


    # HORIZONTAL
    @setting(151, "Horizontal Offset", offset='v', returns='v')
    def horizontal_offset(self, c, offset=None):
        """
        Set or query the horizontal offset.
        Arguments:
            offset (float): the horizontal offset (in seconds).
        Returns:
            (float): the horizontal offset in (in seconds).
        """
        return self.selectedDevice(c).horizontal_offset(offset)

    @setting(152, "Horizontal Scale", scale='v', returns='v')
    def horizontal_scale(self, c, scale=None):
        """
        Set or query the horizontal scale.
        Arguments:
            scale (float): the horizontal scale (in s/div).
        Returns:
            (float): the horizontal scale (in s/div).
        """
        return self.selectedDevice(c).horizontal_scale(scale)


    # ACQUISITION
    @setting(201, "Trace", channel='i', points='i', returns='(*v*v)')
    def get_trace(self, c, channel, points=None):
        """
        Get a trace for a single channel.
        Arguments:
            channel: The channel for which we want to get the trace.
        Returns:
            (*float, *float): (the time
        """
        if points is None:
            return self.selectedDevice(c).get_trace(channel)
        else:
            return self.selectedDevice(c).get_trace(channel, points)


    # MEASURE
    @setting(210, "Measure Start", channel='i', returns='')
    def measure_start(self, c, channel):
        '''
        (re-)start measurement statistics
        (see measure)
        '''
        return self.selectedDevice(c).measure_start(channel)

    @setting(221, "Average Toggle", average_on='b', returns='b')
    def average_toggle(self, c, average_on=None):
        """
        Turn averaging on or off.
        Arguments:
            average_on (bool): If True, turn averaging on.
        Returns:
            (bool): whether averaging is on or off.
        """
        return self.selectedDevice(c).average_toggle(average_on)

    @setting(222, "Average Number", averages='i', returns='i')
    def average_number(self, c, averages=None):
        """
        Set number of averages.
        Arguments:
            averages (int): number of averages.
        Returns:
            (int): number of averages.
        """
        return self.selectedDevice(c).average_number(averages)

    @setting(291, 'Measure Amplitude', channel='i', returns='v')
    def measure_amplitude(self, c, channel):
        """
        Measure channel amplitude.
        Arguments:
            channel (int):      channel to query
        Returns:
                    (float):    the current channel amplitude
        """
        # todo set channel source MEAS:SOUR CH1
        # todo activate statistic MEAS:STAT:ITEM VAMP,CHAN2
        # todo get measurement MEAS:STAT:ITEM? CURR,VAMP
        return self.selectedDevice(c).measure_amplitude(channel)


if __name__ == '__main__':
    from labrad import util
    util.runServer(OscilloscopeServer())
