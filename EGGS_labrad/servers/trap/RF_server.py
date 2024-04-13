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
from AgilentE4434B import AgilentE4434BWrapper
# todo: add notification of listeners & signals


class RFServer(GPIBManagedServer):
    """
    Manages communication with RF Signal Generators.
    """

    name = 'RF Server'

    deviceWrappers = {
        'ROHDE&SCHWARZ SMY01':      SMY01Wrapper,
        'HEWLETT-PACKARD E4434B':   AgilentE4434BWrapper,
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
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).toggle(status)


    # FREQUENCY
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


    # AMPLITUDE
    @setting(311, 'Amplitude', ampl='v', units='s', returns='v')
    def amplitude(self, c, ampl=None, units=None):
        """
        Set/get the signal generator amplitude.
        Arguments:
            ampl    (float) :   the amplitude.
            units   (str)   :   the amplitude units.
                                Can be one of ['DBM', 'VP', or 'VPP'].
        Returns:
                    (float or str) : the amplitude (in dBm).
        """
        return self.selectedDevice(c).amplitude(ampl, units)

    @setting(312, 'Attenuator Hold', status=['b', 'i'], returns='b')
    def att_hold(self, c, status=None):
        """
        Set/get the status of Attenuator Hold.
        Attenuator hold allows for no-glitch amplitude adjustment over a limited range.
        Arguments:
            status  (bool) : the Attenuator Hold status.
        Returns:
                    (bool) : the Attenuator Hold status.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).att_hold(status)

    @setting(321, 'ALC Toggle', status=['b', 'i'], returns='b')
    def alc_toggle(self, c, status=None):
        """
        Set/get the status of Automatic Level Control (ALC).
        Arguments:
            status  (bool) : the ALC status.
        Returns:
                    (bool) : the ALC status.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).alc_toggle(status)

    @setting(322, 'ALC Auto Toggle', status=['b', 'i'], returns='b')
    def alc_auto_toggle(self, c, status=None):
        """
        Set/get the status of Automatic Search for ALC.
        Arguments:
            status  (bool) : the Automatic Search status.
        Returns:
                    (bool) : the Automatic Search status.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).alc_auto_toggle(status)

    @setting(323, 'ALC Search', returns='')
    def alc_search(self, c):
        """
        Run power search for Automatic Level Control (ALC).
        Note: ALC must be off for the search to run.
        """
        self.selectedDevice(c).alc_search()


    '''
    MODULATION
    '''
    @setting(411, 'Modulation Frequency', freq='v', returns='v')
    def mod_frequency(self, c, freq=None):
        """
        Get/set modulation frequency.
        Arguments:
            freq    (float) : the modulation frequency (in Hz).
        Returns:
                    (float) : the modulation frequency (in Hz).
        """
        return self.selectedDevice(c).mod_frequency(freq)

    @setting(412, 'Modulation Toggle', status=['b', 'i'], returns='b')
    def mod_toggle(self, c, status=None):
        """
        Toggle modulation.
        Arguments:
            status  (bool) : the modulation status.
        Returns:
                    (bool) : the modulation status.
        """
        return self.selectedDevice(c).mod_toggle(status)


    # AMPLITUDE MODULATION
    @setting(421, 'AM Toggle', status=['b', 'i'], returns='b')
    def am_toggle(self, c, status=None):
        """
        Toggle amplitude modulation.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).am_toggle(status)

    @setting(422, 'AM Depth', depth='v', returns='v')
    def am_depth(self, c, depth=None):
        """
        Get/set amplitude modulation depth.
        Arguments:
            depth   (float) : the modulation depth (in %).
        Returns:
                    (float) : the modulation depth (in %).
        """
        return self.selectedDevice(c).am_depth(depth)

    @setting(423, 'AM Frequency', freq='v', returns='v')
    def am_frequency(self, c, freq=None):
        """
        Get/set the amplitude modulation frequency.
        Arguments:
            freq    (float) : the modulation frequency (in Hz).
        Returns:
                    (float) : the modulation frequency (in Hz).
        """
        return self.selectedDevice(c).am_frequency(freq)


    # FREQUENCY MODULATION
    @setting(431, 'FM Toggle', status=['b', 'i'], returns='b')
    def fm_toggle(self, c, status=None):
        """
        Toggle frequency modulation.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).fm_toggle(status)

    @setting(432, 'FM Deviation', dev='v', returns='v')
    def fm_deviation(self, c, dev=None):
        """
        Get/set frequency modulation deviation.
        Arguments:
            dev     (float) : the modulation deviation (in Hz).
        Returns:
                    (float) : the modulation deviation (in Hz).
        """
        return self.selectedDevice(c).fm_deviation(dev)

    @setting(433, 'FM Frequency', freq='v', returns='v')
    def fm_frequency(self, c, freq=None):
        """
        Get/set the frequency modulation frequency.
        Arguments:
            freq    (float) : the modulation frequency (in Hz).
        Returns:
                    (float) : the modulation frequency (in Hz).
        """
        return self.selectedDevice(c).fm_frequency(freq)


    # PHASE MODULATION
    @setting(441, 'PM Toggle', status=['b', 'i'], returns='b')
    def pm_toggle(self, c, status=None):
        """
        Toggle phase modulation.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).pm_toggle(status)

    @setting(442, 'PM Deviation', dev='v', returns='v')
    def pm_deviation(self, c, dev=None):
        """
        Get/set phase modulation deviation.
        Arguments:
            dev     (float) : the modulation deviation (in rad).
        Returns:
                    (float) : the modulation deviation (in rad).
        """
        return self.selectedDevice(c).pm_deviation(dev)

    @setting(443, 'PM Frequency', freq='v', returns='v')
    def pm_frequency(self, c, freq=None):
        """
        Get/set the phase modulation frequency.
        Arguments:
            freq    (float) : the modulation frequency (in Hz).
        Returns:
                    (float) : the modulation frequency (in Hz).
        """
        return self.selectedDevice(c).pm_frequency(freq)


if __name__ == '__main__':
    from labrad import util
    util.runServer(RFServer())
