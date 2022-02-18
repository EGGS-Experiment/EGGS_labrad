"""
### BEGIN NODE INFO
[info]
name = Shutter Server
version = 1.0.0
description = Controls the 3D-printed Arduino shutters.
instancename = Shutter Server

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

from EGGS_labrad.servers import SerialDeviceServer

TERMINATOR = '\r\n'


class ShutterServer(SerialDeviceServer):
    """
    Controls the 3D-printed Arduino shutters.
    """

    name = 'Shutter Server'
    regKey = 'ShutterServer'
    serNode = 'MongKok'
    port = None

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
    util.runServer(ShutterServer())