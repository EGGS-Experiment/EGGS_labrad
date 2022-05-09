"""
Base class for building PyQt5 GUI clients for LabRAD.
"""
from os import _exit, environ
from inspect import getmembers
from abc import ABC, abstractmethod
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients.utils import createTrunk
from EGGS_labrad.clients.Widgets import QInitializePlaceholder, QClientMenuHeader

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


    # INITIALIZATION
    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        # core attributes
        self.reactor = reactor
        self.cxn = cxn
        self.parent = parent
        self.guiEnable = True
        # get core servers in addition to whichever servers are specified
        core_servers = {'registry': 'Registry', 'dv': 'Data Vault'}
        self.servers.update(core_servers)
        # show placeholder GUI while we initialize
        #self.gui = QInitializePlaceholder()
        #self.gui.show()
        # initialization sequence
        print("Starting client...")
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._getgui)
        # initData has to be before initGUI otherwise signals will be active
        # while we set initial values, causing the slots to trigger
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)
        d.addCallback(self._connectHeader)


    # STARTUP DISPATCHERS
    @inlineCallbacks
    def _connectLabrad(self):
        """
        Creates an asynchronous connection to core labrad servers
        and sets up server connection signals.
        """
        print("\tConnecting to LabRAD..")
        # only create connection if we aren't instantiated with one
        if not self.cxn:
            if self.LABRADHOST is None:
                self.LABRADHOST = environ['LABRADHOST']
            if self.LABRADPASSWORD is None:
                self.LABRADPASSWORD = environ['LABRADPASSWORD']
            from labrad.wrappers import connectAsync
            print("\t\tEstablishing connection to LabRAD manager @{:s}...".format(self.LABRADHOST))
            self.cxn = yield connectAsync(self.LABRADHOST, name=self.name, password=self.LABRADPASSWORD)
        else:
            print("\t\tLabRAD connection already provided.")
        # set self.servers as class attributes
        print("\t\tGetting required servers...")
        for var_name, server_name in self.servers.items():
            try:
                setattr(self, var_name, self.cxn[server_name])
            except Exception as e:
                setattr(self, var_name, None)
                print('\t\tServer unavailable:', server_name)
        # server connections
        print("\t\tConnecting to LabRAD manager signals...")
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self._serverConnect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self._serverDisconnect, source=None, ID=9898989 + 1)
        print("\tFinished connecting to LabRAD.")
        return self.cxn

    @inlineCallbacks
    def _initClient(self, cxn):
        print("\tInitializing client...")
        try:
            yield self.initClient()
        except Exception as e:
            print('\tError in initClient:', e)
            self.guiEnable = False
        else:
            print("\tSuccessfully initialized client.")
        return cxn

    @inlineCallbacks
    def _initData(self, cxn):
        print("\tGetting default values...")
        try:
            yield self.initData()
        except Exception as e:
            self.guiEnable = False
            print('\tError in initData:', e)
        else:
            print("\tSuccessfully retrieved default values.")
        return cxn

    @inlineCallbacks
    def _getgui(self, cxn):
        print("\tStarting up GUI...")
        # run after initClient so we can get configs or variables from labrad
        try:
            # close placeholder GUI
            #self.gui.hide()
            #self.gui = None
            yield self.getgui()
            #self.gui.show()
            print("\tSuccessfully started up GUI.")
        except Exception as e:
            # just quit if we can't get GUI otherwise we freeze since we don't have a reactor to work with
            print("\tFatal error: unable to start up GUI.")
            print(e)
            print("Exiting...")
            _exit(0)
        # get all widgets that aren't QClientMenuHeaders so we can lock them
        from PyQt5.QtWidgets import QWidget
        isWidgetNotHeader = lambda obj: isinstance(obj, QWidget) and (not isinstance(obj, QClientMenuHeader))
        self._all_widgets = dict(getmembers(self.gui, isWidgetNotHeader))
        return cxn

    @inlineCallbacks
    def _initGUI(self, cxn):
        print("\tInitializing GUI...")
        try:
            yield self.initGUI()
        except Exception as e:
            self.guiEnable = False
            print('\tError in initGUI:', e)
        # make GUI visible at end so user can at least see that we have a problem
        self.gui.show()
        # reenable GUI upon completion of initialization
        if self.guiEnable:
            print("\tGUI initialization successful.")
            # we don't need to enable here since we start up already enabled
        else:
            self._enableAllExceptHeader(False)
        return cxn

    def _connectHeader(self, cxn):
        """
        Check if a client has a QClientMenuHeader and attempt to connect to it.
        This allows us to break out special client-related functions onto
        the GUI and thus allowing users access.

        For example, this allows users to restart the client in the event of
        errors.
        """
        try:
            # todo: don't connect serial and polling if not a device server (e.g. stability client)
            # check if any members of the GUI are QClientMenuHeaders
            isQClientMenuHeader = lambda obj: isinstance(obj, QClientMenuHeader)
            QClientMenuHeader_list = getmembers(self.gui, isQClientMenuHeader)
            # check that the GUI has a QClientMenuHeader
            if len(QClientMenuHeader_list) > 0:
                # initialize the QClientMenuHeader
                menuHeader_name, menuHeader_object = QClientMenuHeader_list[0]
                menuHeader_object.addFile(self)
                # search client servers for SerialDeviceServers, PollingServers, and GPIBManagedDeviceServers
                for server_nickname in self.servers.keys():
                    server_object = getattr(self, server_nickname)
                    # create appropriate submenu
                    if "Serial Query" in server_object.settings.keys():
                        menuHeader_object.addSerial(server_object)
                    if "Polling" in server_object.settings.keys():
                        menuHeader_object.addPolling(server_object)
                    if "GPIB Query" in server_object.settings.keys():
                        menuHeader_object.addGPIB(server_object)
        except Exception as e:
            print("\t", e)
            print("Error connecting to QClientMenuHeader in GUI.")
        return cxn


    # SHUTDOWN
    def close(self):
        print("Shutting down...")
        try:
            print("\tClosing connection to LabRAD...")
            self.cxn.disconnect()
            print("\tStopping reactor...")
            if self.reactor.running:
                self.reactor.stop()
        except Exception as e:
            print(e)
        _exit(0)


    # SLOTS
    @inlineCallbacks
    def _serverConnect(self, c, message):
        server_name = message[1]
        # refresh so we can check if all necessary servers are there
        yield self.cxn.refresh()
        try:
            server_ind = list(self.servers.values()).index(server_name)
            print(server_name + ' reconnected.')
            # set server if connecting for first time
            server_nickname = list(self.servers.keys())[server_ind]
            if getattr(self, server_nickname) is None:
                setattr(self, server_nickname, self.cxn[server_name])
                print('Connecting for first time:', server_name)
            # check if all required servers exist
            if all(server_names.lower().replace(' ', '_') in self.cxn.servers for server_names in self.servers.values()):
                print('Enabling client.')
                # redo initClient to reconnect to signals
                yield self._initClient(self.cxn)
                # redo initData to get new state of server
                yield self._initData(self.cxn)
                self._enableAllExceptHeader(True)
        except ValueError:
            pass
        except Exception as e:
            print(e)

    def _serverDisconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers.values():
            print(server_name + ' disconnected, disabling client.')
            self._enableAllExceptHeader(False)


    # HELPER
    def _restart(self):
        """
        Restarts the GUI client.
        """
        print('Restarting client ...')
        # todo: maybe move this to a permanent startup sequence?
        self.gui.setVisible(False)
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._getgui)
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)
        d.addCallback(self._connectHeader)
        print('Finished restart.')

    def _enableAllExceptHeader(self, status):
        """
        Locks/unlocks all widgets in the GUI that aren't QClientMenuHeaders.
        Arguments:
            status  (bool)  : whether to enable or disable the widgets.
        """
        for widget_object in self._all_widgets.values():
            widget_object.setEnabled(status)


    # SUBCLASSED FUNCTIONS
    def initClient(self):
        """
        To be subclassed.
        Called after _connectLabrad.
        Should be used to get necessary servers, setup listeners,
        do polling, and other labrad stuff.
        """
        pass

    @abstractmethod
    def getgui(self):
        """
        To be subclassed.
        Called after initClient.
        Used to instantiate a GUI class with arbitrary configuration settings.
        This function is called here to
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
