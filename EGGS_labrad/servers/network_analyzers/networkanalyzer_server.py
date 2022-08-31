"""
### BEGIN NODE INFO
[info]
name = Network Analyzer Server
version = 1.1.0
description = Talks to network analyzers.

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
from HP8714ES import HP8714ESWrapper


# cmds
# SENSe (averaging/config etc)
# SOURce (rf poewr output/atten etc)
# CALCulate (marker)
# TRACe (trace)

class NetworkAnalyzerServer(GPIBManagedServer):
    """
    Manages communication with all network analyzers.
    """

    name = 'Network Analyzer Server'

    deviceWrappers = {
        '"HEWLETT-PACKARD 8714ES': HP8714ESWrapper  # yes, i know the " in front is weird but it works
    }


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the network analyzer to factory settings.
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

    @setting(13, "Autoset", returns='')
    def autoset(self, c):
        """
        Automatically set the amplitude and frequency to
        view the dominant signal.
        """
        dev = self.selectedDevice(c)
        yield dev.autoset()


    # ATTENUATION
    @setting(21, "Preamplifier", status=['b', 'i'], returns='b')
    def preamplifier(self, c, status=None):
        """
        Enable/disable the preamplifier.
        Arguments:
            status  (bool): the status of the preamplifier.
        Returns:
                    (bool): the status of the preamplifier.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
        return self.selectedDevice(c).preamplifier(status)


    # OUTPUT
    @setting(31, "Output Toggle", status=['b', 'i'], returns='b')
    def outputToggle(self, c, status=None):
        """
        Enable/disable RF output.
        Arguments:
            status  (bool): the RF output status.
        Returns:
                    (bool): the RF output status.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
        return self.selectedDevice(c).outputToggle(status)


    # SWEEP
    @setting(41, "Sweep Mode", mode='s', returns='s')
    def sweepMode(self, c, mode=None):
        """
        Get/set the sweep mode.
        Arguments:
            status  (bool): the sweep mode.
        Returns:
                    (bool): the sweep mode.
        """
        return self.selectedDevice(c).sweepMode(mode)


    # FREQUENCY RANGE
    @setting(111, "Frequency Start", freq='v', returns='v')
    def frequencyStart(self, c, freq=None):
        """
        Get/set the start frequency.
        Arguments:
            freq    (float): the start frequency (in Hz).
        Returns:
                    (float): the start frequency (in Hz).
        """
        return self.selectedDevice(c).frequencyStart(freq)

    @setting(112, "Frequency Stop", freq='v', returns='v')
    def frequencyStop(self, c, freq=None):
        """
        Get/set the stop frequency.
        Arguments:
            freq    (float): the stop frequency (in Hz).
        Returns:
                    (float): the stop frequency (in Hz).
        """
        return self.selectedDevice(c).frequencyStop(freq)

    @setting(113, "Frequency Center", freq='v', returns='v')
    def frequencyCenter(self, c, freq=None):
        """
        Get/set center frequency.
        Arguments:
            freq    (float): the center frequency (in Hz).
        Returns:
                    (float): the center frequency (in Hz).
        """
        return self.selectedDevice(c).frequencyCenter(freq)

    @setting(114, "Frequency Span", span='v', returns='v')
    def frequencySpan(self, c, span=None):
        """
        Get/set the frequency span.
        Arguments:
            span    (float): the frequency span (in Hz).
        Returns:
                    (float): the frequency span (in Hz).
        """
        return self.selectedDevice(c).frequencySpan(span)


    # MARKER SETUP
    @setting(311, "Marker Toggle", channel='i', status=['b', 'i'], returns='b')
    def markerToggle(self, c, channel, status=None):
        """
        Enable/disable a marker channel.
        Arguments:
            channel (int): the marker channel to get/set.
            status  (bool): whether the marker is on/off.
        Returns:
                    (bool): whether the marker is on/off.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
        return self.selectedDevice(c).markerToggle(channel, status)

    @setting(312, "Marker Tracking", channel='i', status=['b', 'i'], returns='i')
    def markerTracking(self, c, channel, status=None):
        """
        Enable/disable marker tracking.
        Arguments:
            channel (int): the marker channel.
            status  (bool): whether tracking is enabled.
        Returns:
                    (bool): whether tracking is enabled.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
        return self.selectedDevice(c).markerTracking(channel, status)

    @setting(313, "Marker Function", channel='i', mode='s', returns='i')
    def markerFunction(self, c, channel, mode=None):
        """
        Get/set the readout function of a marker channel.
        Can be one of ['OFF', 'MAX', 'MIN', 'TARG', 'BWID', 'NOTCH'].
        Arguments:
            channel (int): the marker channel to get/set.
            mode    (int): the readout mode of the channel.
        Returns:
                    (int): the readout mode of the channel.
        """
        return self.selectedDevice(c).markerFunction(channel, mode)

    @setting(321, "Marker Measure", channel='i', returns='v')
    def markerMeasure(self, c, channel):
        """
        Read the value of a marker channel.
            The function to be measured by the marker is configured in marker_function.
        Arguments:
            channel (int): the marker channel to get/set.
        Returns:
                    (float): the amplitude of the marker (in dBm).
        """
        return self.selectedDevice(c).markerMeasure(channel)


    # PEAK
    @setting(411, "Peak Search", status=['b', 'i'], returns='b')
    def peakSearch(self, c, status=None):
        """
        Get/set the status of signal tracking.
        If a marker is already active, signal tracking will
        use that marker to set the center frequency.
        If a marker does not already exist, signal tracking
        will create a marker and use it to set the center frequency.

        Arguments:
            status  (bool): the status of signal tracking.
        Returns:
                    (bool): the status of signal tracking.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
        return self.selectedDevice(c).peakSearch(status)

    @setting(412, "Peak Set", status='v', returns='b')
    def peakSet(self, c, status=None):
        """
        Arguments:
            status  (bool): the status of signal tracking.
        Returns:
                    (bool): the status of signal tracking.
        """
        # todo
        return self.selectedDevice(c).peakSet(status)

    @setting(421, "Peak Next", status='v', returns='b')
    def peakNext(self, c, status=None):
        """
        Arguments:
            status  (bool): the status of signal tracking.
        Returns:
                    (bool): the status of signal tracking.
        """
        # todo
        return self.selectedDevice(c).peakNext(status)


    # BANDWIDTH
    @setting(511, "Bandwidth Sweep Time", time='v', returns='v')
    def bandwidthSweepTime(self, c, time=None):
        """
        Get/set the sweep time.
        Arguments:
            time    (float): the sweep time (in s).
        Returns:
                    (float): the sweep time (in s).
        """
        return self.selectedDevice(c).bandwidthSweepTime(time)

    @setting(521, "Bandwidth Resolution", bw='i', returns='i')
    def bandwidthResolution(self, c, bw=None):
        """
        Get/set the resolution bandwidth.
        Increasing resolution bandwidth increases the sweep time.
        Arguments:
            bw      (int): the resolution bandwidth (in Hz).
        Returns:
                    (int): the resolution bandwidth (in Hz).
        """
        return self.selectedDevice(c).bandwidthResolution(bw)


    # TRACE
    @setting(911, "Trace", channel='i', returns='(*v*v)')
    def getTrace(self, c, channel):
        """
        Get the current trace.
        Arguments:
            channel (int): the trace channel to get/set.
        Returns:
                    (*v, *v): the trace.
        """
        return self.selectedDevice(c).getTrace(channel)



if __name__ == '__main__':
    from labrad import util
    util.runServer(NetworkAnalyzerServer())
