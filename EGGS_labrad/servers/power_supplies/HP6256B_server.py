"""
### BEGIN NODE INFO
[info]
name = HP6256B Server
version = 1.0.0
description = Uses the ARTIQ DAC to communicate with the HP6256B power supply for loading via getter.
instancename = HP6256BServer

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from twisted.internet.defer import returnValue
from EGGS_labrad.servers import ARTIQServer

_HP6256B_AMPS_TO_mV = 2.5e-2


class HP6256B_server(ARTIQServer):
    """
    Uses the ARTIQ DAC to communicate with the HP6256B power supply for loading via getter.
    """

    name = 'HP6256B Server'
    regKey = 'HP6256BServer'

    DAC_channel = 10

    def initServer(self):
        super().initServer()
        # get the ARTIQ server
        try:
            self.artiq = self.client.artiq_server
            self.current = 0
            # initialize the DAC? calibrate & set up the channel?
        except Exception as e:
            print(e)
            raise


    # VOLTAGE
    @setting(211, 'Current', amps='v', returns=['v'])
    def current(self, c, amps=None):
        """
        Set the current in amps.
        Args:
            amps    (float) : the output current of the power supply
        Returns:
                    (float) : the output current of the power supply
        """
        if amps is not None:
            if (amps < 0) and (amps > 23):
                self.current = amps
                yield self.artiq.dac_set(self.DAC_channel, amps * _HP6256B_AMPS_TO_mV, 'v')
            else:
                raise Exception('Error: invalid current.')
        returnValue(self.current)


if __name__ == '__main__':
    from labrad import util
    util.runServer(HP6256B_server())