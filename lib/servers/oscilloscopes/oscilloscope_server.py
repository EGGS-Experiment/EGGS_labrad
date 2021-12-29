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
from labrad.server import setting
from labrad.gpib import GPIBManagedServer
from twisted.internet.defer import inlineCallbacks, returnValue

# import device wrapper
from RigolDS1000Z import RigolDS1000ZWrapper
from TektronixMSO2000 import TektronixMSO2000Wrapper


class OscilloscopeServer(GPIBManagedServer):
    """
    Manages communication with all oscilloscopes.
    """

    name = 'Oscilloscope Server'

    deviceWrappers = {
        'RIGOL TECHNOLOGIES DS1104Z Plus': RigolDS1000ZWrapper,
        'TEKTRONIX MSO2024B': TektronixMSO2000Wrapper
        'KEYSIGHT DS1204G': KeysightDS1204GWrapper
    }


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """Reset the oscilloscopes to factory settings."""
        dev = self.selectedDevice(c)
        yield dev.reset()

    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        """Clear device status buffers."""
        dev = self.selectedDevice(c)
        yield dev.clear_buffers()


    # CHANNEL
    @setting(100, "Channel Info", channel='i', returns='(vvvvsvss)')
    def channel_info(self, c, channel):
        """
        Get channel information.
        Args:
            channel (int): channel to get information on

        Returns:
            Tuple of (attenuation, termination, scale, position, coupling, bwLimit, invert, units)
        """
        return self.selectedDevice(c).channel_info(channel)

    @setting(111, "Channel Coupling", channel='i', coup='s', returns='s')
    def channel_coupling(self, c, channel, coup=None):
        """
        Set or query channel coupling.
        Args:
            channel (int): Which channel to set coupling.
            coup (str): Coupling, 'AC' or 'DC'. If None (the default) just query
                the coupling without setting it.

        Returns:
            string indicating the channel's coupling.
        """
        return self.selectedDevice(c).channel_coupling(channel, coup)

    @setting(112, "Channel Scale", channel='i', scale='v[V]', returns='v[V]')
    def channel_scale(self, c, channel, scale=None):
        """
        Get or set the vertical scale.
        Args:
            channel (int): The channel to get or set.
            scale (Value[V]): The vertical scale, i.e. voltage per division. If
                None (the default), we just query.

        Returns:
            (Value[V]): The vertical scale.
        """
        return self.selectedDevice(c).channel_scale(channel, scale)

    @setting(113, "Channel Probe", channel='i', factor='i', returns = ['s'])
    def channel_probe(self, c, channel, factor = None):
        """
        Get/set the probe attenuation factor.
        Args:
            channel (int): the channel to get/set
            factor (int): the probe attenuation factor

        Returns:
            (string): the probe attenuation factor
        """
        return self.selectedDevice(c).channel_probe(channel, factor)

    @setting(114, "Channel Toggle", channel='i', state='b', returns='b')
    def channel_toggle(self, c, channel, state=None):
        """
        Set or query channel on/off state.
        Args:
            channel (int): Which channel.
            state (bool): True->On, False->Off. If None (default), then we
                only query the state without setting it.

        Returns:
            (bool): The channel state.
        """
        return self.selectedDevice(c).channel_toggle(channel, state)

    @setting(115, "Channel Invert", channel='i', invert='b', returns='b')
    def channel_invert(self, c, channel, invert=None):
        """
        Get or set channel inversion.
        Args:
            channel (int):
            invert (bool): True->invert channel, False->do not invert channel.
                If None (the default), then we only query the inversion.

        Returns:
            (int): 0: not inverted, 1: inverted.
        """
        return self.selectedDevice(c).channel_invert(channel, invert)

    @setting(116, "Channel Offset", channel='i', offset='v[]', returns='v[]')
    def channel_offset(self, c, channel, offset=None):
        """
        Get or set the vertical offset.
        Args:
            channel (int): Which channel to get/set.
            offset (float): Vertical offset in units of divisions. If None,
                (the default), then we only query.

        Returns:
            (float): Vertical offset in units of divisions.
        """
        return self.selectedDevice(c).channel_offset(channel, offset)

    @setting(117, "Channel Termination", channel='i', term='i', returns='i')
    def channel_termination(self, c, channel, term=None):
        """
        Set channel termination.
        Args:
            channel (int): Which channel to set termination.
            term (int): Termination in Ohms. Either 50 or 1,000,000.
        """
        return self.selectedDevice(c).channel_termination(channel, term)


    # TRIGGER
    @setting(131, "Trigger Channel", source='s', returns='s')
    def trigger_channel(self, c, source=None):
        """
        Set or query trigger channel.
        Args:
            source (str): 'EXT', 'LINE', 'CHANX' where X is channel number. If
                None (the default) then we just query.

        Returns:
            (str): Trigger source.
        """
        return self.selectedDevice(c).trigger_channel(source)

    @setting(132, "Trigger Slope", slope='s', returns='s')
    def trigger_slope(self, c, slope=None):
        """
        Set or query trigger slope.
        Args:
            slope (str): Trigger slope. If None, the default, we just query.
                Allowed values are 'POS' and 'NEG'.

        Returns:
            (str): The trigger slope.
        """
        return self.selectDevice(c).trigger_slope(slope)

    @setting(133, "Trigger Level", level='v[V]', returns='v[V]')
    def trigger_level(self, c, level=None):
        """
        Set or query the trigger level.
        Args:
            level (Value[V]): Trigger level. If None (the default), we just
                query.

        Returns:
            (Value[V]): The trigger level.
        """
        return self.selectedDevice(c).trigger_level(level)

    @setting(134, "Trigger Mode", mode='s', returns='s')
    def trigger_mode(self, c, mode=None):
        """
        Set or query the trigger mode.
        Args:
            mode (str): The trigger mode to set. If None, we just query.

        Returns (str): The trigger mode.
        """
        return self.selectedDevice(c).trigger_mode(mode)


    # HORIZONTAL
    @setting(151, "Horizontal Offset", position='v[]', returns='v[]')
    def horiz_offset(self, c, position=None):
        """
        Set or query the horizontal offset.
        Args:
            position (float): Horizontal offset in units of division.

        Returns:
            (float): The horizontal offset in units of divisions.
        """
        return self.selectedDevice(c).horiz_offset(position)

    @setting(152, "Horizontal ", scale='v[s]', returns='v[s]')
    def horiz_scale(self, c, scale=None):
        """
        Set or query the horizontal scale.
        Args:
            scale (Value[s]): Horizontal scale, i.e. time per division. If None,
                (the default), then we just query.

        Returns:
            (Value[s]): The horizontal scale.
        """
        return self.selectedDevice(c).horiz_scale(scale)


    # ACQUISITION
    @setting(201, "Trace", channel='i', returns='(*v*v)')
    def get_trace(self, c, channel):
        """
        Get a trace for a single channel.
        Args:
            channel: The channel for which we want to get the trace.

        Returns:
            Tuple of ((ValueArray[s]) Time axis, (ValueArray[V]) Voltages).
        """
        return self.selectedDevice(c).get_trace(channel)

    @setting(210, "Measure Start ", returns='')
    def measure_start(self, c):
        '''
        (re-)start measurement statistics
        (see measure)
        '''
        return self.selectedDevice(c).measure_start(channel)

    @setting(221, "Average Toggle", average_on='b', returns='b')
    def average_toggle(self, c, average_on=None):
        """
        Turn averaging on or off.
        Args:
            average_on (bool): If True, turn averaging on.

        Returns:
            (bool): Whether averaging is one or off.
        """
        return self.selectedDevice(c).average_toggle(average_on)

    @setting(222, "Average Number", averages='i', returns='i')
    def average_number(self, c, averages=None):
        """
        Set number of averages.
        Args:
            averages (int): Number of averages.

        Returns:
            (int): Number of averages.
        """
        return self.selectedDevice(c).average_number(averages)


if __name__ == '__main__':
    from labrad import util
    util.runServer(OscilloscopeServer())