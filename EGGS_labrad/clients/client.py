"""
Base class for building PyQt5 GUI clients for LabRAD.
"""

# imports
from os import _exit, environ
from datetime import datetime
from abc import ABC, abstractmethod
from twisted.internet.defer import inlineCallbacks

__all__ = ["GUIClient", "RecordingClient"]



class GUIClient(ABC):
    """
    Creates a client from a single GUI file.
    """

    name = None
    servers = {}
    gui = None

    # STARTUP
    def __init__(self, reactor, cxn=None, parent=None):
        # set client variables
        super().__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.parent = parent
        self.getgui()
        # initialization sequence
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._initData)
        d.addCallback(self._initializeGUI)

    @inlineCallbacks
    def _connectLabrad(self):
        """
        Creates an asynchronous connection to core labrad servers
        and sets up server connection signals.
        """
        # only create connection if we aren't instantiated with one
        if not self.cxn:
            LABRADHOST = environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync('localhost', name=self.name)

        # set self.servers as class attributes
        self.servers['registry'] = 'registry'
        self.servers['datavault'] = 'data_vault'
        for var_name, server_name in self.servers.items():
            try:
                setattr(self, var_name, self.cxn[server_name])
            except Exception as e:
                setattr(self, var_name, None)
        # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        return self.cxn

    @inlineCallbacks
    def _initClient(self, cxn):
        try:
            yield self.initClient()
        except Exception as e:
            self.gui.setEnabled(False)
            print('Error in initClient.')
            print(e)
        return cxn

    @inlineCallbacks
    def _initData(self, cxn):
        try:
            yield self.initData()
        except Exception as e:
            self.gui.setEnabled(False)
            print('Error in initData.')
            print(e)
        return cxn

    @inlineCallbacks
    def _initializeGUI(self, cxn):
        try:
            yield self.initializeGUI()
        except Exception as e:
            self.gui.setEnabled(False)
            print('Error in initializeGUI.')
            print(e)
        return cxn


    # SHUTDOWN
    def close(self):
        try:
            self.cxn.disconnect()
            if self.reactor.running:
                self.reactor.stop()
            _exit(0)
        except Exception as e:
            print(e)
            _exit(0)


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        yield self.cxn.refresh()
        try:
            server_ind = list(self.servers.values()).index(server_name)
            print(server_name + ' reconnected.')
            # set server if connecting for first time
            server_nickname = list(self.servers.keys())[server_ind]
            if getattr(self, server_nickname) is None:
                setattr(self, server_nickname, self.cxn[server_name])
            # check if all required servers exist
            if all(server_names.lower().replace(' ', '_') in self.cxn.servers for server_names in self.servers.values()):
                print('Enabling client.')
                yield self._initData(self.cxn)
                self.gui.setEnabled(True)
        except ValueError as e:
            pass
        except Exception as e:
            print(e)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers.values():
            print(server_name + ' disconnected, disabling client.')
            self.gui.setEnabled(False)


    # SUBCLASSED FUNCTIONS
    @property
    @abstractmethod
    def getgui(self):
        """
        To be subclassed.
        Called during __init__.
        Used to return an instantiated GUI class so it can be used by GUIClient.
        """
        pass

    def initClient(self):
        """
        To be subclassed.
        Called after _connectLabrad.
        Should be used to get necessary servers, setup listeners,
        do polling, and other labrad stuff.
        """
        pass

    def initData(self):
        """
        To be subclassed.
        Called after initClient and upon server reconnections.
        Should be used to get initial state variables from servers.
        """
        pass

    def initializeGUI(self):
        """
        To be subclassed.
        Called after initData.
        Should be used to connect GUI signals to slots and initialize the GUI.
        """
        pass



class RecordingClient(GUIClient):
    """
    Supports client data taking.
    """

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        # set recording variables
        self.c_record = self.cxn.context()
        self.recording = False

    def _createDatasetTitle(self, *args, **kwargs):
        # set up datavault
        date = datetime.now()
        year = str(date.year)
        month = '{:02d}'.format(date.month)

        trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
        trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
        return ['', year, month, trunk1, trunk2]

    #todo: data vault function?

    # SHUTDOWN
    @inlineCallbacks
    def closeEvent(self, event):
        polling, _ = yield self.server.polling()
        if polling:
            yield self.server.polling(False)
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


    # SUBCLASSED FUNCTIONS
    def record(self, *args, **kwargs):
        """
        Creates a new dataset to record data
        and sets recording status.
        """
        pass
