"""
### BEGIN NODE INFO
[info]
name = FMA1700A Server
version = 1.0.0
description = Gets data from an Arduino which breaks out the FMA1700A flow signal.
instancename = FMA1700A Server

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

from EGGS_labrad.servers import PollingServer, SerialDeviceServer

TERMINATOR = '\r\n'


class FMA1700AServer(SerialDeviceServer, PollingServer):
    """
    Gets data from an Arduino which breaks out the FMA1700A flow signal.
    """

    name = 'FMA1700A Server'
    regKey = 'FMA1700A Server'
    serNode = 'MongKok'
    port = 'COM58'

    timeout = WithUnit(5.0, 's')
    baudrate = 115200


    # SIGNALS
    flow_update = Signal(999999, 'signal: flow update', 'v')


    # FLOW
    @setting(111, 'Flow', returns='v')
    def flow(self, c):
        """
        Get flow as a percentage of maximum.
        Returns:
                (v)  : percent of maximum flow
        """
        yield self.ser.acquire()
        yield self.ser.write('F?' + TERMINATOR)
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = float(resp.strip())
        self.flow_update(resp)
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for flow readout.
        """
        # query
        yield self.flow(None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(FMA1700AServer())