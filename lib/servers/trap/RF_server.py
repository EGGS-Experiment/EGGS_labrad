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

from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.gpib import GPIBManagedServer
from labrad.server import setting

#import wrappers
from SMY01 import SMY01Wrapper

class RFServer(GPIBManagedServer):
    """Manages communication with RF Signal Generators."""

    name = 'RF Server'

    deviceWrappers = {
        'ROHDE&SCHWARZ SMY01': SMY01Wrapper,
    }

    # GENERAL
    @setting(111, 'Reset', returns='')
    def reset(self, c):
        """Reset the signal generator."""
        dev = self.selectedDevice(c)
        yield dev.reset()

    @setting(112, 'Status', returns='s')
    def status(self, c):
        """Get status of the signal generator."""
        dev = self.selectedDevice(c)
        yield dev.status()

    @setting(121, 'Toggle', onoff='b', returns='b')
    def toggle(self, c, onoff=None):
        """Turn the signal generator on/off."""
        dev = self.selectedDevice(c)
        return dev.toggle(onoff)


    # WAVEFORM
    @setting(211, 'Frequency', freq='v', returns='v')
    def frequency(self, c, freq=None):
        """Set the signal generator frequency."""
        dev = self.selectedDevice(c)
        return dev.freq(freq)

    @setting(121, 'Amplitude', ampl='v', returns='v')
    def amplitude(self, c, ampl=None):
        """Set the signal generator amplitude."""
        dev = self.selectedDevice(c)
        return dev.ampl(ampl)


    # MODULATION
    @setting(311, 'AM Toggle', onoff='b', returns='b')
    def am_toggle(self, c, onoff=None):
        """Toggle amplitude modulation."""
        dev = self.selectedDevice(c)
        return dev.fm_toggle(onoff)

    @setting(312, 'AM Frequency', freq='v', returns='v')
    def am_freq(self, c, freq=None):
        """Set amplitude modulation frequency."""
        dev = self.selectedDevice(c)
        return dev.am_freq(freq)

    @setting(313, 'AM Depth', depth='v', returns='v')
    def am_depth(self, c, depth=None):
        """Set amplitude modulation depth."""
        dev = self.selectedDevice(c)
        return dev.am_depth(depth)

    @setting(321, 'FM Toggle', onoff='b', returns='b')
    def fm_toggle(self, c, onoff=None):
        """Toggle frequency modulation."""
        dev = self.selectedDevice(c)
        return dev.fm_toggle(onoff)

    @setting(322, 'FM Frequency', freq='v', returns='v')
    def fm_freq(self, c, freq=None):
        """Set frequency modulation frequency."""
        dev = self.selectedDevice(c)
        return dev.fm_freq(freq)

    @setting(321, 'PM Toggle', onoff='b', returns='b')
    def fm_toggle(self, c, onoff=None):
        """Toggle phase modulation."""
        dev = self.selectedDevice(c)
        return dev.pm_toggle(onoff)

    @setting(322, 'PM Frequency', freq='v', returns='v')
    def fm_freq(self, c, freq = None):
        """Set phase modulation frequency."""
        dev = self.selectedDevice(c)
        return dev.pm_freq(freq)


if __name__ == '__main__':
    from labrad import util
    util.runServer(RFServer())