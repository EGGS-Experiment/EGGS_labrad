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
# imports
from labrad.gpib import GPIBManagedServer
from labrad.server import setting

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
        """Reset the signal generator."""
        yield self.selectedDevice(c).reset()

    @setting(121, 'Toggle', onoff='b', returns='s')
    def toggle(self, c, onoff=None):
        """Turn the signal generator on/off."""
        return self.selectedDevice(c).toggle(onoff)


    # WAVEFORM
    @setting(211, 'Frequency', freq='v', returns='v')
    def frequency(self, c, freq=None):
        """Set the signal generator frequency (in Hz)."""
        return self.selectedDevice(c).frequency(freq)

    @setting(212, 'Amplitude', ampl='v', units='s', returns='v')
    def amplitude(self, c, ampl=None, units=None):
        """
        Set/get the signal generator amplitude.
        Returns the amplitude in dBm.
        """
        return self.selectedDevice(c).amplitude(ampl, units)


    # MODULATION
    @setting(311, 'Modulation Frequency', freq='v', returns='v')
    def mod_freq(self, c, freq=None):
        """Set modulation frequency (in Hz)."""
        return self.selectedDevice(c).mod_freq(freq)

    @setting(312, 'AM Toggle', onoff='b', returns='s')
    def am_toggle(self, c, onoff=None):
        """Toggle amplitude modulation."""
        return self.selectedDevice(c).am_toggle(onoff)

    @setting(313, 'AM Depth', depth='v', returns='v')
    def am_depth(self, c, depth=None):
        """Set amplitude modulation depth (in %)."""
        return self.selectedDevice(c).am_depth(depth)

    @setting(321, 'FM Toggle', onoff='b', returns='s')
    def fm_toggle(self, c, onoff=None):
        """Toggle frequency modulation."""
        return self.selectedDevice(c).fm_toggle(onoff)

    @setting(322, 'FM Deviation', dev='v', returns='v')
    def fm_dev(self, c, dev=None):
        """Set frequency modulation deviation (in Hz)."""
        return self.selectedDevice(c).fm_dev(dev)

    @setting(323, 'PM Toggle', onoff='b', returns='s')
    def pm_toggle(self, c, onoff=None):
        """Toggle phase modulation."""
        return self.selectedDevice(c).pm_toggle(onoff)

    @setting(324, 'PM Deviation', dev='v', returns='v')
    def pm_dev(self, c, dev=None):
        """Set phase modulation deviation (in Hz)."""
        return self.selectedDevice(c).pm_dev(dev)


if __name__ == '__main__':
    from labrad import util
    util.runServer(RFServer())
