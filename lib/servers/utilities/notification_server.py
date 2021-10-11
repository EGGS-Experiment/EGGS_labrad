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
from labrad.server import LabradServer
from twisted.internet.defer import inlineCallbacks, returnValue
import smtplib
from email.message import EmailMessage

SERVERNAME = 'Notification Server'

class NotificationServer(LabradServer):
    name = 'Notification Server'
    regKey = 'NotificationServer'

    @inlineCallbacks
    def initServer(self):
        pass

    #setup email
    @setting(111, 'email', msg='s', recipient = 's',returns='')
    def email(self, c, msg, recipient):
        """
        Send an email
        Args:
            msg         (str): the message to send
            recipient   (str): the recipient's email address
        """
        email_msg = EmailMessage()
        email_msg.set_content(msg)
        email_msg['To'] = recipient

        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()

if __name__ == "__main__":
    from labrad import util
    util.runServer(NotificationServer())
