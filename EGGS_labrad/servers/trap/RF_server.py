"""
### BEGIN NODE INFO
[info]
name = RF Server
version = 1.0
description = Talks to Trap RF Generator

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

from SMY01 import SMY01Wrapper


class RFServer(GPIBManagedServer):
    """
    Manages communication with RF Signal Generators.
    """

    name = 'RF Server'

    deviceWrappers = {
        'ROHDE&SCHWARZ SMY01': SMY01Wrapper,
    }


    # GENERAL
    @setting(111, 'Reset', returns='')
    def reset(self, c):
        """
        Reset the signal generator.
        """
        yield self.selectedDevice(c).reset()

    @setting(121, 'Toggle', status=['b', 'i'], returns='b')
    def toggle(self, c, status=None):
        """
        Turn the signal generator on/off.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).toggle(status)


    # WAVEFORM
    @setting(211, 'Frequency', freq='v', returns='v')
    def frequency(self, c, freq=None):
        """
        Get/set the signal generator frequency (in Hz).
        Arguments:
            freq    (float) : the frequency (in Hz).
        Returns:
                    (float) : the frequency (in Hz).
        """
        return self.selectedDevice(c).frequency(freq)

    @setting(212, 'Amplitude', ampl='v', units='s', returns='v')
    def amplitude(self, c, ampl=None, units=None):
        """
        Set/get the signal generator amplitude.
        Arguments:
            ampl    (float) : the amplitude (units to be specified).
        Returns:
                    (float) : the amplitude (in dBm).
        """
        return self.selectedDevice(c).amplitude(ampl, units)


    # MODULATION
    @setting(311, 'Modulation Frequency', freq='v', returns='v')
    def mod_freq(self, c, freq=None):
        """
        Get/set modulation frequency.
        Arguments:
            freq    (float) : the modulation frequency (in Hz).
        Returns:
                    (float) : the modulation frequency (in Hz).
        """
        return self.selectedDevice(c).mod_freq(freq)

    @setting(312, 'Toggle Modulation', status=['b', 'i'], returns='b')
    def mod_toggle(self, c, status=None):
        """
        Toggle modulation.
        Arguments:
            status  (bool) : the modulation status.
        Returns:
                    (bool) : the modulation status.
        """
        return self.selectedDevice(c).mod_toggle(status)

    @setting(321, 'Toggle AM', status=['b', 'i'], returns='b')
    def am_toggle(self, c, status=None):
        """
        Toggle amplitude modulation.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).am_toggle(status)

    @setting(322, 'Modulation AM Depth', depth='v', returns='v')
    def am_depth(self, c, depth=None):
        """
        Get/set amplitude modulation depth.
        Arguments:
            depth   (float) : the modulation depth (in %).
        Returns:
                    (float) : the modulation depth (in %).
        """
        return self.selectedDevice(c).am_depth(depth)

    @setting(331, 'Toggle FM', status='b', returns='b')
    def fm_toggle(self, c, status=None):
        """
        Toggle frequency modulation.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).fm_toggle(status)

    @setting(332, 'Modulation FM Deviation', dev='v', returns='v')
    def fm_dev(self, c, dev=None):
        """
        Get/set frequency modulation deviation.
        Arguments:
            dev     (float) : the modulation deviation (in Hz).
        Returns:
                    (float) : the modulation deviation (in Hz).
        """
        return self.selectedDevice(c).fm_dev(dev)

    @setting(341, 'Toggle PM', status=['b', 'i'], returns='b')
    def pm_toggle(self, c, status=None):
        """
        Toggle phase modulation.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).pm_toggle(status)

    @setting(342, 'Modulation PM Deviation', dev='v', returns='v')
    def pm_dev(self, c, dev=None):
        """
        Get/set phase modulation deviation.
       Arguments:
            dev     (float) : the modulation deviation (in rad).
        Returns:
                    (float) : the modulation deviation (in rad).
        """
        return self.selectedDevice(c).pm_dev(dev)


    # FEEDBACK
    @setting(411, 'Toggle Feedback Amplitude', status=['b', 'i'], returns='b')
    def feedback_toggle(self, c, status=None):
        """
        Toggle amplitude feedback.
        Uses an external DC signal to adjust the output signal amplitude.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).feedback_amplitude_toggle(status)

    @setting(412, 'Feedback Amplitude Depth', depth='v', returns='v')
    def feedback_amplitude_depth(self, c, depth=None):
        """
        Get/set amplitude feedback depth.
        Changes the amount to which a DC feedback signal
        adjusts the amplitude (i.e. 0-100%).
        Arguments:
            depth   (float) : the feedback depth (in %).
        Returns:
                    (float) : the feedback depth (in %).
        """
        return self.selectedDevice(c).feedback_amplitude_depth(depth)


if __name__ == '__main__':
    from labrad import util
    util.runServer(RFServer())
