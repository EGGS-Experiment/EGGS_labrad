"""
Base class for building PyQt5 GUI clients for LabRAD.
"""
from os import _exit, environ
from abc import ABC, abstractmethod
from time import localtime, strftime
from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.utils import createTrunk

__all__ = ["GUIClient", "RecordingGUIClient"]


class GUIClient(ABC):
    """
    Creates a client from a single GUI file.
    """

    # client parameters
    name = None
    servers = {}
    gui = None
    # LabRAD connection parameters
    LABRADHOST = None
    LABRADPASSWORD = None

    # STARTUP
    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        # core attributes
        self.reactor = reactor
        self.cxn = cxn
        self.parent = parent
        self.guiEnable = True
        self.logPreamble = "%H:%M:%S [{:s}]".format(self.name)
        # initialization sequence
        print(strftime(self.logPreamble, localtime()), "Starting up client...")
        #self.getgui() # tmp original
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._getgui)
        # initData has to be before initGUI otherwise signals will be active
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)

    @inlineCallbacks
    def _connectLabrad(self):
        """
        Creates an asynchronous connection to core labrad servers
        and sets up server connection signals.
        """
        print(strftime(self.logPreamble, localtime()), "Connecting to LabRAD...")
        # only create connection if we aren't instantiated with one
        if not self.cxn:
            if self.LABRADHOST is None:
                self.LABRADHOST = environ['LABRADHOST']
            if self.LABRADPASSWORD is None:
                self.LABRADPASSWORD = environ['LABRADPASSWORD']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(self.LABRADHOST, name=self.name, password=self.LABRADPASSWORD)
        print(strftime(self.logPreamble, localtime()), "Connection successful.")
        # set self.servers as class attributes
        print(strftime(self.logPreamble, localtime()), "Getting required servers...")
        self.servers['registry'] = 'registry'
        self.servers['dv'] = 'data_vault'
        for var_name, server_name in self.servers.items():
            try:
                setattr(self, var_name, self.cxn[server_name])
            except Exception as e:
                setattr(self, var_name, None)
                print(strftime(self.logPreamble, localtime()), 'Server unavailable:', server_name)
        # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        return self.cxn

    @inlineCallbacks
    def _initClient(self, cxn):
        # disable GUI until initialization finishes
        #self.gui.setEnabled(False) # tmp original
        print(strftime(self.logPreamble, localtime()), "Initializing client...")
        try:
            yield self.initClient()
        except Exception as e:
            print(strftime(self.logPreamble, localtime()), 'Error in initClient:', e)
            self.guiEnable = False
        else:
            print(strftime(self.logPreamble, localtime()), "Successfully initialized client.")
        return cxn

    @inlineCallbacks
    def _getgui(self, cxn):
        try:
            # get GUI after initClient so we can call any config
            # or initialization variables we need
            yield self.getgui()
            self.gui.show()
        except Exception as e:
            print(e)
            # exit if we can't get GUI otherwise
            # we freeze since we don't have a reactor
            # to work with
            _exit(0)
        return cxn

    @inlineCallbacks
    def _initData(self, cxn):
        print(strftime(self.logPreamble, localtime()), "Getting default values...")
        try:
            yield self.initData()
        except Exception as e:
            self.guiEnable = False
            print(strftime(self.logPreamble, localtime()), 'Error in initData:', e)
        else:
            print(strftime(self.logPreamble, localtime()), "Successfully retrieved default values.")
        return cxn

    @inlineCallbacks
    def _initGUI(self, cxn):
        print(strftime(self.logPreamble, localtime()), "Initializing GUI...")
        try:
            yield self.initGUI()
        except Exception as e:
            self.guiEnable = False
            print(strftime(self.logPreamble, localtime()), 'Error in initGUI:', e)
        # reenable GUI upon completion of initialization
        if self.guiEnable:
            print(strftime(self.logPreamble, localtime()), "GUI initialization successful.")
            self.gui.setEnabled(True)
        else:
            self.gui.setEnabled(False)
        return cxn

    #@inlineCallbacks
    def _restart(self):
        """
        Reinitializes the GUI Client.
        """
        print(strftime(self.logPreamble, localtime()), 'Restarting client ...')
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)
        print(strftime(self.logPreamble, localtime()), 'Finished restart.')

    def _thre(self):
        """
        Reinitializes the GUI Client.
        """
        print(strftime(self.logPreamble, localtime()), 'Restarting client ...')
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)
        print(strftime(self.logPreamble, localtime()), 'Finished restart.')


    # SHUTDOWN
    def close(self):
        try:
            self.cxn.disconnect()
            if self.reactor.running:
                self.reactor.stop()
            _exit(0)
        except Exception as e:
            print(strftime(self.logPreamble, localtime()), e)
            _exit(0)


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        yield self.cxn.refresh()
        try:
            server_ind = list(self.servers.values()).index(server_name)
            print(strftime(self.logPreamble, localtime()), server_name + ' reconnected.')
            # set server if connecting for first time
            server_nickname = list(self.servers.keys())[server_ind]
            if getattr(self, server_nickname) is None:
                setattr(self, server_nickname, self.cxn[server_name])
                print(strftime(self.logPreamble, localtime()), 'Connecting for first time:', server_name)
            # check if all required servers exist
            if all(server_names.lower().replace(' ', '_') in self.cxn.servers for server_names in self.servers.values()):
                print(strftime(self.logPreamble, localtime()), 'Enabling client.')
                # redo initClient to reconnect to signals
                yield self._initClient(self.cxn)
                # redo initData to get new state of server
                yield self._initData(self.cxn)
                self.gui.setEnabled(True)
        except ValueError as e:
            pass
        except Exception as e:
            print(strftime(self.logPreamble, localtime()), e)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers.values():
            print(strftime(self.logPreamble, localtime()), server_name + ' disconnected, disabling client.')
            self.gui.setEnabled(False)


    # SUBCLASSED FUNCTIONS
    #@property
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

    def initGUI(self):
        """
        To be subclassed.
        Called after initData.
        Should be used to connect GUI signals to slots and initialize the GUI.
        """
        pass


class RecordingGUIClient(GUIClient):
    """
    Supports client polling and data taking.
    """

    def __init__(self, reactor, cxn=None, parent=None):
        # add data vault as a necessary server first
        self.servers['dv'] = 'Data Vault'
        super().__init__(reactor, cxn, parent)
        # set recording variables
        self.c_record = self.cxn.context()
        self.recording = False
        self.starttime = None
        # start device polling only if not already started

    @inlineCallbacks
    def _initClient(self, cxn):
        super()._initClient(cxn)
        # todo: polling on each server
        # makes any polling servers start polling
        for server_nickname in self.servers.keys():
            # todo: check if server is pollingserver type
            server = getattr(self, server_nickname)
            if hasattr(server, 'polling'):
                poll_params = yield server.polling()
                if not poll_params[0]:
                    yield self.tt.polling(True, 5.0)
        return cxn

    @inlineCallbacks
    def _record(self):
        """

        """
        yield self._createDataset()

    @inlineCallbacks
    def _createDataset(self, *args, **kwargs):
        """

        """
        # create trunk for dataset
        createTrunk(self.name)
        # set up datavault
        self.recording = status
        if self.recording:
            self.starttime = time()
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new('Lakeshore 336 Temperature Controller', [('Elapsed time', 't')],
                                       [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'),
                                        ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')], context=self.c_record)


    # SUBCLASSED FUNCTIONS
    def record(self, *args, **kwargs):
        """
        Creates a new dataset to record data
        and sets recording status.
        """
        pass
