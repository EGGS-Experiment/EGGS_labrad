"""
### BEGIN NODE INFO
[info]
name = H11890 Server
version = 1.0.0
description = Controls the Hamamatsu H11890-210 PMT
instancename = H11890 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.units import WithUnit
from labrad.server import setting, Signal

from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer
from EGGS_labrad.lib.servers.polling_server import PollingServer


class H11890Server(SerialDeviceServer, PollingServer):
    """
    Controls the Hamamatsu H11890-210 PMT.
    """

    name = 'H11890 Server'
    regKey = 'H11890Server'
    serNode = 'MongKok'
    port = 'COM58'

    timeout = WithUnit(3.0, 's')
    baudrate = 9600

    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', '(ii)')
    temperature_update = Signal(999998, 'signal: temperature update', '(iiii)')


    # STATUS
    @setting(11, 'Status', returns='*s')
    def status(self, c):
        """
        Get system status.
        """
        # create message
        cmd_msg = b'STA'

    @setting(12, 'Toggle', status='b', returns='b')
    def toggle(self, c, status=None):
        """
        Toggle the PMT.
        Arguments:
            status  (bool)  : the power status of the PMT
        Returns:
                    (bool)  : the power status of the PMT
        """
        # create message
        cmd_msg = b'STA'


    # GATING
    @setting(211, 'Gate Time', time_ms='v', returns='v')
    def gateTime(self, c, time_ms=None):
        """
        Set the gate time.
        Arguments:
            time_ms (int)   : the gate time in ms
        Returns:
                    (int)   : the gate time in ms
        """
        # create message
        pass

    # ACQUIRE
    @setting(311, 'Acquire', returns='v')
    def acquire(self, c):
        """
        Start the PMT run.
        Arguments:
        Returns:
        """
        # create message
        pass

    @setting(311, 'Correction', status='b', returns='b')
    def acquire(self, c, status=None):
        """
        Start/stop correction mode.
        Arguments:
            status  (bool)  : whether to stop or start correction mode.
        Returns:
            status  (bool)  : whether to stop or start correction mode.
        """
        # create message
        pass


if __name__ == '__main__':
    from labrad import util
    util.runServer(H11890Server())