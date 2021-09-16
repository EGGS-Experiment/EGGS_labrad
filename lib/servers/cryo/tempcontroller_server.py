"""
### BEGIN NODE INFO
[info]
name = Temperature Controller Server
version = 0.9.0
description = Talks to Temperature Controllers

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from __future__ import absolute_import

from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.gpib import GPIBManagedServer
from labrad.server import setting
from lakeshore336 import Lakeshore336Wrapper

class TemperatureControllerServer(GPIBManagedServer):
    """
    Manages communication with temperature controllers.
    """

    name = 'Temperature Controller Server'

    deviceWrappers = {
        'LSCI MODEL 336 LSA2CBI': Lakeshore336Wrapper
    }

    #SYSTEM
    @setting(11, returns='')
    def reset(self, c):
        """Reset to factory settings."""
        dev = self.selectedDevice(c)
        yield dev.reset()

    @setting(12, returns='')
    def clear_buffers(self, c):
        """Clear device status buffers."""
        dev = self.selectedDevice(c)
        yield dev.clear_buffers()


    #READ TEMPERATURE
    @setting(111, channel='s', returns='*1v')
    def read_temperature(self, c, channel):
        """
        Get sensor temperature

        Args:
            channel (str): sensor channel to measure

        Returns:
            (*float): sensor temperature in Kelvin
        """
        return self.selectedDevice(c).read_temperature(channel)


if __name__ == '__main__':
    from labrad import util
    util.runServer(TemperatureControllerServer())