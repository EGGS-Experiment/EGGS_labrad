"""
Base class for building PyQt5 GUI clients for LabRAD
"""

#imports
import time
import datetime as datetime

from PyQt5.QtWidgets import QWidget

from twisted.internet.defer import inlineCallbacks

__all__ = ["GUIClient"]


class GUIClient(object):
    """
    Creates a client from a single GUI file.
    """

    name = None

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.reactor = reactor
        self.servers = []
        # initialization sequence
        d = self._connectLabrad()
        d.addCallback(self.initClient)
        d.addCallback(self.initializeGUI)

    # SETUP
    @inlineCallbacks
    def _connectLabrad(self):
        """
        Creates an asynchronous connection to core labrad servers
        and sets up server connection signals.
        """
        # only create connection if we aren't instantiated with one
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync('localhost', name=self.name)

        # ensure base servers are online
        self.servers.extend(['Registry', 'Data Vault'])
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
        except Exception as e:
            print(e)
            raise

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)

        return self.cxn

    def initClient(self, cxn):
        """
        To be subclassed.
        Called after _connectLabrad.
        Should be used to get necessary servers,
        setup listeners, do polling, and other labrad stuff.
        WARNING: cxn must be an argument and returned to enforce execution order.
        """
        return self.cxn

    def initializeGUI(self, cxn):
        """
        To be subclassed.
        Called after initClient.
        Should be used to connect GUI signals to slots
        and set up initial data.
        WARNING: cxn must be an argument and returned to enforce execution order.
        """
        return self.cxn


    # SIGNALS
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)


    # OTHER
    @inlineCallbacks
    def record(self, status, *args, **kwargs):
        """
        Creates a new dataset to record data
        and sets recording status.
        """
        self.recording = status
        if self.recording:
            self.starttime = time.time()
            date = datetime.datetime.now()
            year = str(date.year)
            month = '%02d' % date.month  # Padded with a zero if one digit
            day = '%02d' % date.day  # Padded with a zero if one digit
            hour = '%02d' % date.hour  # Padded with a zero if one digit
            minute = '%02d' % date.minute  # Padded with a zero if one digit

            trunk1 = year + '_' + month + '_' + day
            trunk2 = self.name + '_' + hour + ':' + minute
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new(self.name, [('Elapsed time', 't')],
                              [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_record)
            # todo: fix

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()
