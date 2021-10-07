"""
### BEGIN NODE INFO
[info]
name = Wavemeter Server
version = 1.0
description =
instancename = Wavemeter Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from labrad.server import LabradServer, Signal
from twisted.internet.defer import returnValue
from labrad.support import getNodeName
import time

SERVERNAME = 'Wavemeter Server'

class WavemeterServer(LabradServer):
    name = 'Wavemeter Server'

    @inlineCallbacks
    def initServer(self):
        pass

    # ***
    @setting(111, 'fd', msg='s', returns='')
    def fd(self, c, msg=None):
        """
        fd
        """
        pass

if __name__ == "__main__":
    from labrad import util
    util.runServer(WavemeterServer())
