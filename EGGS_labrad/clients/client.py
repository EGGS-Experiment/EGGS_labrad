"""
Base class for building PyQt5 GUI clients for LabRAD.
"""

# imports
from datetime import datetime
from twisted.internet.defer import inlineCallbacks, ensureDeferred

__all__ = ["GUIClient", "RecordingClient"]


class GUIClient(object):
    """
    Creates a client from a single GUI file.
    """

    name = None
    servers = {}
    #gui = None

    # STARTUP
    def __init__(self, reactor, cxn=None, parent=None):
        # set parent to GUI file
        #th1 = type(self.__class__.__name__, (self.gui, object), dict(self.__class__.__dict__))
        #super(self.__class__).__init__()
        #super(GUIClient, self).__init__()
        # set client variables
        super().__init__()
        #self.gui.__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.parent = parent

        # initialization sequence
        d = self._connectLabrad()
        d.addCallback(self.initClient)
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)


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

        # set self.servers as class attributes
        self.servers['registry'] = 'Registry'
        self.servers['datavault'] = 'Data Vault'
        try:
            for var_name, server_name in self.servers.items():
                server =self.cxn[server_name]
                yield setattr(self, var_name, server)
        except Exception as e:
            print(e)
            raise

        # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        return self.cxn


    # SHUTDOWN
    def close(self):
        # stop polling all required servers
        for var_name in self.servers.keys():
            try:
                server = getattr(self, var_name)
                polling, _ = server.polling()
                if polling:
                    server.polling(False)
            except Exception as e:
                pass
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


    # SIGNALS
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers.values():
            print(server_name + ' reconnected.')
            self.initData()
            # check to see if all necessary servers are connected
            print('Enabling client.')
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers.values():
            print(server_name + ' disconnected, disabling client.')
            self.setEnabled(False)



    # SUBCLASSED FUNCTIONS
    def initClient(self, cxn):
        """
        To be subclassed.
        Called after _connectLabrad.
        Should be used to get necessary servers, setup listeners,
        do polling, and other labrad stuff.
        WARNING: cxn must be an argument and returned to enforce execution order.
        """
        return self.cxn

    def initData(self, cxn):
        """
        To be subclassed.
        Called after initClient and upon server reconnections.
        Should be used to get initial state variables from servers.
        WARNING: cxn must be an argument and returned to enforce execution order.
        """
        return self.cxn

    def initializeGUI(self, cxn):
        """
        To be subclassed.
        Called after initData.
        Should be used to connect GUI signals to slots and initialize the GUI.
        WARNING: cxn must be an argument and returned to enforce execution order.
        """
        return self.cxn



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
