import sys
import logging

__all__ = ["labradLogFormatter", "_LoggerWriter", "setupLogging"]


labradLogFormatter = logging.Formatter(
    "%(asctime)s [%(name)-15.15s] [%(sender_host)-15.15s] [%(sender_name)-25.25s] [%(levelname)-10.10s]  %(message)s"
)


class _LoggerWriter:
    """
    Redirects stdout to logger.
    """

    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message != '\n':
            self.level(message)

    def flush(self):
        self.level(sys.stderr)


def setupLogging(sender=None):
    """
    Sets up the logger.
    Arguments:
        sender  : the sender.
    """
    from os import environ
    from socket import SOCK_STREAM
    from logging.handlers import SysLogHandler
    from rfc5424logging import Rfc5424SysLogHandler

    # create syslog handler
    syslog_socket = (environ['LABRADHOST'], int(environ['EGGS_LABRAD_SYSLOG_PORT']))
    syslog_handler = SysLogHandler(address=syslog_socket)
    syslog_handler.setFormatter(labradLogFormatter)

    # create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(labradLogFormatter)

    # create rfc5424 handler
    loki_handler = Rfc5424SysLogHandler(
        address=('192.168.1.48', 1514),
        socktype=SOCK_STREAM,
        enterprise_id=88888
    )

    # create logger
    logging.basicConfig(level=logging.DEBUG, handlers=None)
    logger = logging.getLogger("labrad.client")

    # don't propagate log events to root logger
    logger.propagate = False

    # add handlers
    logger.addHandler(syslog_handler)
    logger.addHandler(console_handler)
    logger.addHandler(loki_handler)

    # redirect print statements to logger
    #sys.stdout = _LoggerWriter(logger.info)
    