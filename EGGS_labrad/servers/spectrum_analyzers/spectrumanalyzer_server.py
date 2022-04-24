"""
### BEGIN NODE INFO
[info]
name = Spectrum Analyzer Server
version = 1.1.0
description = Talks to spectrum analyzers.

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
from RigolDSA800 import RigolDSA800Wrapper


class SpectrumAnalyzerServer(GPIBManagedServer):
    """
    Manages communication with all spectrum analyzers.
    """

    name = 'Spectrum Analyzer Server'

    deviceWrappers = {
        'RIGOL TECHNOLOGIES DSA815': RigolDSA800Wrapper
    }


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the spectrum analyzer to factory settings.
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

    @setting(22, "Attenuation", status='b', returns='b')
    def preamplifier(self, c, status):
        """
        Enable/disable the preamplifier.
        Arguments:
            status  (bool): the status of the preamplifier.
        Returns:
                    (bool): the status of the preamplifier.
        """
        # todo
        return self.selectedDevice(c).preamplifier(status)


    # FREQUENCY RANGE
    @setting(111, "Frequency Start", freq='v', returns='v')
    def frequencyStart(self, c, freq):
        """
        Get/set the start frequency.
        Arguments:
            freq    (float): the start frequency (in Hz).
        Returns:
                    (float): the start frequency (in Hz).
        """
        return self.selectedDevice(c).frequencyStart(freq)

    @setting(112, "Frequency Stop", freq='v', returns='v')
    def frequencyStop(self, c, freq):
        """
        Get/set the stop frequency.
        Arguments:
            freq    (float): the stop frequency (in Hz).
        Returns:
                    (float): the stop frequency (in Hz).
        """
        return self.selectedDevice(c).frequencyStop(freq)

    @setting(113, "Frequency Center", freq='v', returns='v')
    def frequencyCenter(self, c, freq):
        """
        Get/set center frequency.
        Arguments:
            freq    (float): the center frequency (in Hz).
        Returns:
                    (float): the center frequency (in Hz).
        """
        return self.selectedDevice(c).frequencyCenter(freq)


    # AMPLITUDE
    @setting(211, "Amplitude Reference", ampl='v', returns='v')
    def amplitudeReference(self, c, ampl):
        """
        Get/set the amplitude reference level (i.e. the top of the trace).
        Arguments:
            ampl    (float): the reference level (in dBm).
        Returns:
                    (float): the reference level (in dBm).
        """
        return self.selectedDevice(c).amplitudeReference(ampl)

    @setting(212, "Amplitude Offset", ampl='v', returns='v')
    def amplitudeOffset(self, c, ampl):
        """
        Get/set the amplitude offset level. #todo better note and understand
        Arguments:
            ampl    (float): the offset level (in dBm).
        Returns:
                    (float): the offset level (in dBm).
        """
        return self.selectedDevice(c).amplitudeOffset(ampl)

    @setting(213, "Amplitude Scale", factor='v', returns='v')
    def amplitudeScale(self, c, factor):
        """
        Get/set the amplitude scale.
        Arguments:
            factor  (float): the amplitude scale (in dBm/div).
        Returns:
                    (float): the amplitude scale (in dBm/div).
        """
        return self.selectedDevice(c).amplitudeScale(factor)


    # MARKER SETUP
    @setting(311, "Marker Toggle", number='i', status=['b', 'i'], returns='b')
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

    @setting(312, "Marker Trace", channel='i', trace='i', returns='i')
    def markerTrace(self, c, channel, trace=None):
        """
        Get/set the trace for a marker channel to follow.
        Arguments:
            channel (int): the marker channel to get/set.
            status  (bool): whether the marker is on/off.
        Returns:
                    (bool): whether the marker is on/off.
        """
        return self.selectedDevice(c).markerTrace(channel, trace)

    @setting(313, "Marker Mode", channel='i', mode='i', returns='b')
    def markerMode(self, c, channel, mode=None):
        """
        Get/set the marker mode.
            0: Position (normal).
            1: Delta
            2: Delta Pair
            3: Span Pair
        Arguments:
            channel (int): the marker channel to get/set.
            mode    (int): the marker mode, can be one of (0, 1, 2, 3).
        Returns:
                    (int): the marker mode.
        """
        return self.selectedDevice(c).markerMode(channel, mode)

    @setting(314, "Marker Readout", channel='i', mode='i', returns='v')
    def markerReadout(self, c, channel, mode=None):
        """
        Get/set the readout mode of a marker channel.
            0: Frequency
            1: Time
            2: Inverse time
            3: Period
        Arguments:
            channel (int): the marker channel to get/set.
            mode    (int): the readout mode of the channel.
        Returns:
                    (int): the readout mode of the channel.
        """
        return self.selectedDevice(c).markerRead(channel, mode)

    @setting(315, "Marker Position", channel='i', pos='b', returns='b')
    def markerPosition(self, c, channel, pos=None):
        """
        Get/set the x-position of a normal mode marker.
        Arguments:
            channel (int): the marker channel to get/set.
            status  (bool): whether the marker is on/off.
        Returns:
                    (bool): whether the marker is on/off.
        """
        return self.selectedDevice(c).markerPosition(channel, pos)

    @setting(316, "Marker Value", channel='i', returns='v')
    def markerValue(self, c, channel):
        """
        Get the value of a marker channel.
        Arguments:
            channel (int): the marker channel to get/set.
        Returns:
                    (float): the y-position of the marker (in dBm).
        """
        return self.selectedDevice(c).markerValue(channel)


    # MARKER FUNCTIONS
    # todo

    # PEAK
    @setting(411, "Peak Search", status='v', returns='b')
    def peakSearch(self, c, status):
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
        return self.selectedDevice(c).peakSearch(status)

    @setting(412, "Peak Set", status='v', returns='b')
    def peakSet(self, c, status):
        """
        todo
        Arguments:
            status  (bool): the status of signal tracking.
        Returns:
                    (bool): the status of signal tracking.
        """
        return self.selectedDevice(c).peakSet(status)

    @setting(421, "Peak Next", status='v', returns='b')
    def peakNext(self, c, status):
        """
        todo
        Arguments:
            status  (bool): the status of signal tracking.
        Returns:
                    (bool): the status of signal tracking.
        """
        return self.selectedDevice(c).peakNext(status)


    # BANDWIDTH
    @setting(511, "Marker Readout", time='v', returns='v')
    def markerReadout(self, c, time=None):
        """
        Get/set the sweep time.
        Arguments:
            time    (float): the sweep time (in s).
        Returns:
                    (float): the sweep time (in s).
        """
        return self.selectedDevice(c).markerRead(mode)

    @setting(511, "Bandwidth Resolution", bw='i', returns='i')
    def bandwidthResolution(self, c, bw=None):
        """
        Get/set the resolution bandwidth.
        Arguments:
            bw      (int): the resolution bandwidth (in Hz).
        Returns:
                    (int): the resolution bandwidth (in Hz).
        """
        return self.selectedDevice(c).bandwidthResolution(bw)

    @setting(511, "Bandwidth Video", bw='i', returns='i')
    def bandwidthResolution(self, c, bw=None):
        """
        Get/set the video bandwidth.
        Arguments:
            bw      (int): the video bandwidth (in Hz).
        Returns:
                    (int): the video bandwidth (in Hz).
        """
        return self.selectedDevice(c).bandwidthVideo(bw)


    # frequency counter?
    # SIGNAL
    @setting(611, "Signal Track", channel='i', status=['b', 'i'], returns='b')
    def signalTrack(self, c, channel, status):
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
        return self.selectedDevice(c).signalTrack(channel, status)


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
    util.runServer(SpectrumAnalyzerServer())
