"""
### BEGIN NODE INFO
[info]
name = Notification Server
version = 1.0
description =
instancename = Notification Server

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
import time

SERVERNAME = 'Notification Server'

class NotificationServer(LabradServer):
    name = 'Notification Server'
    regKey = 'NotificationServer'

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
