"""
### BEGIN NODE INFO
[info]
name = piezo_controller
version = 1.0
description =
instancename = piezo_controller

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.types import Value
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.servers import PollingServer, SerialDeviceServer

TERMINATOR = '\r\n'


class PiezoServer(SerialDeviceServer, PollingServer):
    """
    Connects to the AMO3 voltage box for piezo control.
    """

    name = 'Piezo Server'
    regKey = 'PiezoServer'
    serNode = 'mongkok'
    port = None

    # STATUS

    # POWER





    @setting(101, channel='i', value='b')
    def set_output_state(self, c, channel, value):
        '''
        Turn a channel on or off
        '''
        self.output = value
        dev = self.selectDevice(c)
        yield dev.write('out.w ' + str(channel) + ' ' + str(int(value)) + '\r\n')
        self.current_state[str(channel)][1] = int(value)

    @setting(102, value='b')
    def set_remote_state(self, c, value):
        '''
        Turn the remote mode on
        '''

        dev = self.selectDevice(c)
        yield dev.write('remote.w ' + str(int(value)) + '\r\n')

    @setting(200, channel='i', returns='b')
    def get_output_state(self, c, channel, value):
        '''
        Get the output state of the specified channel. State is unknown when
        server is first started or restarted.
        '''

        return self.current_state[str(channel)][1]

    @setting(201, channel='i', returns='v')
    def get_voltage(self, c, channel):
        return self.current_state[str(channel)][0]


if __name__ == "__main__":
    from labrad import util
    util.runServer(PiezoServer())
