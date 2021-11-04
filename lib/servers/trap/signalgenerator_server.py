"""
### BEGIN NODE INFO
[info]
name = Signal Generator Server
version = 1.0
description = Talks to Trap Signal Generator

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
from RigolDS1000Z import RigolDS1000ZWrapper
from TektronixMSO2000 import TektronixMSO2000Wrapper

class SignalGeneratorServer(GPIBManagedServer):
    """Manages communication with oscilloscopes. ALL the oscilloscopes."""

    name = 'Oscilloscope Server'

    deviceWrappers = {
        'RIGOL TECHNOLOGIES DS1104Z Plus': RigolDS1000ZWrapper,
        'TEKTRONIX MSO2024B': TektronixMSO2000Wrapper
    }

    # SYSTEM
    @setting(11, returns='')
    def reset(self, c):
        """Reset the oscilloscopes to factory settings."""
        dev = self.selectedDevice(c)
        yield dev.reset()

    @setting(12, returns='')
    def clear_buffers(self, c):
        """Clear device status buffers."""
        dev = self.selectedDevice(c)
        yield dev.clear_buffers()


if __name__ == '__main__':
    from labrad import util
    util.runServer(SignalGeneratorServer())