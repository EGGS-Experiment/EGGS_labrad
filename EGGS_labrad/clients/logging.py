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


def setupLogging(logger_name, sender=None):
    """
    Sets up the logger.
    Arguments:
        logger_name : the name of the logger to set up.
        sender      : the sender.
    """
    from os import environ
    from socket import SOCK_STREAM, gethostname
    from logging.handlers import SysLogHandler
    from rfc5424logging import Rfc5424SysLogHandler
    from rfc5424logging.adapter import Rfc5424SysLogAdapter

    # create logger
    logging.basicConfig(level=logging.DEBUG, handlers=None)
    logger = logging.getLogger(logger_name)

    # don't propagate log events to root logger
    logger.propagate = False

    # check if logger already has handlers
    handlers = {}
    for name, logger_class in logging.Logger.manager.loggerDict.items():
        if isinstance(logger_class, logging.Logger) and (name == logger_name):
            for log_handler in logger_class.handlers:
                handlers[logger_name] = log_handler

    # only add handlers if we don't already have some
    if len(handlers) == 0:
        # create syslog handler
        syslog_socket = (environ['LABRADHOST'], int(environ['EGGS_LABRAD_SYSLOG_PORT']))
        syslog_handler = SysLogHandler(address=syslog_socket)
        syslog_handler.setFormatter(labradLogFormatter)

        # create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(labradLogFormatter)

        # create rfc5424 handler
        loki_handler = Rfc5424SysLogHandler(
            address=(environ['LABRADHOST'], 1514),
            socktype=SOCK_STREAM,
            enterprise_id=88888
        )

        # add handlers
        logger.addHandler(syslog_handler)
        logger.addHandler(console_handler)
        logger.addHandler(loki_handler)

    # create custom loghandler so logging labels are specific to each sender
    extraDict = {
        'sender_host': gethostname(),
        'sender_name': sender.__class__.__name__,
    }

    structured_data = {'sender': extraDict.copy()}
    extraDict.update({'structured_data': structured_data})

    # set logger as instance variable
    logger_adapter = Rfc5424SysLogAdapter(logger, extraDict)
    return logger_adapter
