"""
### BEGIN NODE INFO
[info]
name = NotificationServer
version = 1.0
description =
instancename = NotificationServer

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

SERVERNAME = 'NotificationServer'

class NotificationServer(LabradServer):
    name = 'SLSServer'
    regKey = 'SLSServer'
    port = None
    serNode = getNodeName()
    timeout = T.Value(TIMEOUT, 's')

    @inlineCallbacks
    def initServer(self):
        pass

    # ***
    @setting(111, 'email', msg='s', returns='')
    def email(self, c, msg=None):
        """
        Send an email
        """
        pass

if __name__ == "__main__":
    from labrad import util
    util.runServer(NotificationServer())
