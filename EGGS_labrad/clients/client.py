"""
Base classes for building PyQt5 GUI clients for LabRAD.
"""
import sys

from os import _exit, environ
from inspect import getmembers
from abc import ABC, abstractmethod

from twisted.internet.defer import inlineCallbacks
from labrad.logging import setupLogging, _LoggerWriter

from EGGS_labrad.clients.utils import createTrunk
from EGGS_labrad.clients.Widgets import QClientMenuHeader

__all__ = ["GUIClient"]


class GUIClient(ABC):
    """
    Creates a client that connects to LabRAD and has a GUI.
    Does all necessary startup steps under the hood such that the user only
    needs to do implementation-specific initialization.

    Attributes:
        name            (str)               : the name of the GUI client.
        servers         (dict of str: str)  : specifies the LabRAD servers that the client needs and
                                                sets them as instance variables with the name as the key.
        gui             (QWidget)           : the gui object associated with the client.
        LABRADHOST      (str)               : the IP address of the LabRAD manager. If left as None,
                                                it will be set to the LABRADHOST environment variable.
        LABRADPASSWORD  (str)               : the password used to connect to the LabRAD manager. If left as None,
                                                it will be set to the LABRADHOST environment variable.
        createMenu      (bool)              : whether a QClientMenuHeader should be added to the Client.
    """
    # Client parameters
    name = None
    servers = {}
    gui = None

    # LabRAD connection parameters
    LABRADHOST = None
    LABRADPASSWORD = None

    # GUI parameters
    createMenu = True


    # INITIALIZATION
    def __init__(self, reactor, cxn=None, parent=None):
        """
        Basic initialization of class variables and GUI tools.
        """
        super().__init__()
        # core attributes
        self.reactor = reactor
        self.cxn = cxn
        self.parent = parent
        self.guiEnable = True

        # set up logging
        self._setupLogging()

        # get core servers in addition to whichever servers are specified
        core_servers = {'reg': 'Registry', 'dv': 'Data Vault'}
        self.servers.update(core_servers)

        # show placeholder GUI while we initialize
        #self.gui = QInitializePlaceholder()
        #self.gui.show()

        # initialization sequence
        self.logger.info("Starting client...")
        d = self._connectLabrad()
        # note: initClient has to be before getgui, since some GUIs are initialized
        # using configuration objects that are only created during initClient
        d.addCallback(self._initClient)
        d.addCallback(self._getgui)
        # note: initData has to be before initGUI otherwise signals will be active
        # while we set initial values, causing the slots to trigger
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)
        d.addCallback(self._connectHeader)

    def _setupLogging(self):
        """
        Set up the client logger.
        """
        # set logger as instance variable
        self.logger = setupLogging('labrad.client', sender=self)
        # redirect stdout
        sys.stdout = _LoggerWriter(self.logger.info)


    # STARTUP DISPATCHERS
    @inlineCallbacks
    def _connectLabrad(self):
        """
        Creates an asynchronous connection to core LabRAD servers
        and sets up server connection signals.
        """
        self.logger.info("Connecting to LabRAD..")
        # only create connection if we aren't instantiated with one
        if not self.cxn:
            if self.LABRADHOST is None:
                self.LABRADHOST = environ['LABRADHOST']
            if self.LABRADPASSWORD is None:
                self.LABRADPASSWORD = environ['LABRADPASSWORD']
            from labrad.wrappers import connectAsync
            self.logger.debug("Establishing connection to LabRAD manager @{ip_address:s}...".format(ip_address=self.LABRADHOST))
            self.cxn = yield connectAsync(self.LABRADHOST, name=self.name, password=self.LABRADPASSWORD)
        else:
            self.logger.debug("LabRAD connection already provided.")

        # set self.servers as class attributes
        self.logger.debug("Getting required servers...")
        for var_name, server_name in self.servers.items():
            try:
                setattr(self, var_name, self.cxn[server_name])
            except Exception as e:
                setattr(self, var_name, None)
                self.logger.warning("Server unavailable: {_server_name:s}".format(_server_name=server_name))

        # server connections
        self.logger.debug("Connecting to LabRAD manager signals...")
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self._serverConnect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self._serverDisconnect, source=None, ID=9898989 + 1)
        self.logger.info("Finished connecting to LabRAD.")
        return self.cxn

    @inlineCallbacks
    def _initClient(self, cxn):
        self.logger.info("Initializing client...")
        try:
            yield self.initClient()
        except Exception as e:
            self.logger.error("Error in initClient: {error}".format(error=e))
            self.guiEnable = False
        else:
            self.logger.info("Successfully initialized client.")
        return cxn

    @inlineCallbacks
    def _initData(self, cxn):
        self.logger.info("Getting default values...")
        try:
            yield self.initData()
        except Exception as e:
            self.guiEnable = False
            self.logger.error("Error in initData: {error}".format(error=e))
        else:
            self.logger.info("Successfully retrieved default values.")
        return cxn

    @inlineCallbacks
    def _getgui(self, cxn):
        self.logger.info("Starting up GUI...")
        # run after initClient so we can get configs or variables from labrad
        try:
            # close placeholder GUI
            #self.gui.hide()
            #self.gui = None
            yield self.getgui()
            #self.gui.show()
            self.logger.info("Successfully started up GUI.")
        except Exception as e:
            # just quit if we can't get GUI otherwise we freeze since we don't have a reactor to work with
            self.logger.critical("Fatal error: unable to start up GUI: {error}".format(error=e))
            self.logger.critical("Exiting...")
            _exit(0)
        # get all widgets that aren't QClientMenuHeaders so we can lock them
        from PyQt5.QtWidgets import QWidget
        isWidgetNotHeader = lambda obj: isinstance(obj, QWidget) and (not isinstance(obj, QClientMenuHeader))
        self._all_widgets = dict(getmembers(self.gui, isWidgetNotHeader))
        return cxn

    @inlineCallbacks
    def _initGUI(self, cxn):
        self.logger.info("Initializing GUI...")
        try:
            yield self.initGUI()
        except Exception as e:
            self.guiEnable = False
            self.logger.error("Error in initGUI: {error}".format(error=e))

        # make GUI visible at end so user can at least see that we have a problem
        self.gui.show()

        # reenable GUI upon completion of initialization
        if self.guiEnable:
            self.logger.info("GUI initialization successful.")
            # we don't need to enable here since we start up already enabled
        else:
            self._enableAllExceptHeader(False)

        return cxn

    def _connectHeader(self, cxn):
        """
        Check if a client has a QClientMenuHeader and attempt to connect to it.
        This allows us to break out special client-related functions onto
        the GUI and thus allowing users access.

        For example, this allows users to restart the client in the event of errors.
        """
        # don't create menu if createMenu = False
        if not self.createMenu:
            return cxn
        try:
            # check if any members of the GUI are QClientMenuHeaders
            isQClientMenuHeader = lambda obj: isinstance(obj, QClientMenuHeader)
            QClientMenuHeader_list = getmembers(self.gui, isQClientMenuHeader)

            # check that the GUI has a QClientMenuHeader
            if len(QClientMenuHeader_list) > 0:
                self.logger.debug("QClientMenuHeader exists. Attempting to connect...")
                # initialize the QClientMenuHeader
                menuHeader_name, menuHeader_object = QClientMenuHeader_list[0]
                menuHeader_object.addFile(self)

            # otherwise, create and initialize a header here and add it to our gui class
            elif len(QClientMenuHeader_list) == 0:
                self.logger.debug("No QClientMenuHeader exists in the GUI file. Adding one now...")
                menuHeader_object = QClientMenuHeader(cxn=self.cxn, parent=self.gui)
                setattr(self.gui, 'header', menuHeader_object)
                gui_layout = self.gui.layout()
                gui_layout.setMenuBar(menuHeader_object)
                # initialize the QClientMenuHeader
                menuHeader_object.addFile(self)

            # search client servers for SerialDeviceServers, PollingServers, and GPIBManagedDeviceServers
            for server_nickname in self.servers.keys():
                server_object = getattr(self, server_nickname)

                # create appropriate submenus
                if "Serial Query" in server_object.settings.keys():
                    menuHeader_object.addSerial(server_object)
                    menuHeader_object.addCommunication(server_object)
                elif "GPIB Query" in server_object.settings.keys():
                    menuHeader_object.addGPIB(server_object)
                    menuHeader_object.addCommunication(server_object)
                if "Polling" in server_object.settings.keys():
                    menuHeader_object.addPolling(server_object)
            self.logger.debug("Successfully connected to QClientMenuHeader.")
        except Exception as e:
            self.logger.error("Error connecting to QClientMenuHeader: {error}".format(error=e))
        return cxn


    # SHUTDOWN
    def close(self):
        self.logger.info("Shutting down...")
        try:
            self.logger.debug("Closing connection to LabRAD...")
            self.cxn.disconnect()
            self.logger.debug("Stopping reactor...")
            if self.reactor.running:
                self.reactor.stop()
        except Exception as e:
            self.logger.error("Error while shutting down: {error}".format(error=e))
        _exit(0)


    # SLOTS
    @inlineCallbacks
    def _serverConnect(self, c, message):
        server_name = message[1]
        # refresh so we can check if all necessary servers are there
        yield self.cxn.refresh()

        try:
            server_ind = list(self.servers.values()).index(server_name)
            self.logger.debug("{_server:s} reconnected.".format(_server=server_name))

            # set server if connecting for first time
            server_nickname = list(self.servers.keys())[server_ind]
            if getattr(self, server_nickname) is None:
                setattr(self, server_nickname, self.cxn[server_name])
                self.logger.info("Establishing initial connection to: {_server:s}.".format(_server=server_name))

            # check if all required servers exist
            if all(server_names.lower().replace(' ', '_') in self.cxn.servers for server_names in self.servers.values()):
                self.logger.info("All required servers online. Enabling client.")
                # redo initClient to reconnect to signals
                yield self._initClient(self.cxn)
                # redo initData to get new state of server
                yield self._initData(self.cxn)
                self._enableAllExceptHeader(True)
        except ValueError:
            pass
        except Exception as e:
            self.logger.error("Error during {server:s} reconnect: {error}".format(server=server_name, error=e))

    def _serverDisconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers.values():
            self.logger.info("{server:s} disconnected. Disabling client.".format(server=server_name))
            self._enableAllExceptHeader(False)


    # HELPER
    def _restart(self):
        """
        Restarts the GUI client.
        """
        self.logger.info('Restarting client ...')
        self.gui.setVisible(False)
        d = self._connectLabrad()
        d.addCallback(self._initClient)
        d.addCallback(self._getgui)
        d.addCallback(self._initData)
        d.addCallback(self._initGUI)
        d.addCallback(self._connectHeader)
        self.logger.info('Finished restart.')

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
        Should be used to get necessary servers, setup listeners, do polling,
        and other labrad stuff.
        """
        pass

    @abstractmethod
    def getgui(self):
        """
        To be subclassed.
        Called after initClient.
        Used to instantiate a GUI class with arbitrary configuration settings.
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
