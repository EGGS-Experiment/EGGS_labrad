"""
### BEGIN NODE INFO
[info]
name = Electrode Server
version = 1.0
description = Talks to Trap Electrodes

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
from labrad.server import setting, LabradServer

class ElectrodeServer(LabradServer):
    """Manages communication with the trap electrodes."""

    name = 'Electrode Server'

    # deviceWrappers = {
    #     '***todo': SMY01Wrapper,
    # }

    # SYSTEM
    @setting(11, returns='')
    def reset(self, c):
        """Reset the oscilloscopes to factory settings."""
        dev = self.selectedDevice(c)
        yield dev.reset()


    # STATUS
    @setting(111, returns='')
    def clear_buffers(self, c):
        """Clear device status buffers."""
        dev = self.selectedDevice(c)
        yield dev.clear_buffers()


if __name__ == '__main__':
    from labrad import util
    util.runServer(ElectrodeServer())