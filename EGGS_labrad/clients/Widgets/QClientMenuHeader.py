from twisted.internet.defer import inlineCallbacks
from PyQt5.QtWidgets import QMenuBar, QMenu, QAction, QWidgetAction, QDoubleSpinBox

# todo: do menu and actions programmatically
# todo: make prettier
class QClientMenuHeader(QMenuBar):
    """
    A client menu header that breaks out core server functions.
    Designed to be initialized by a GUIClient.
    """

    def __init__(self):
        super().__init__()
        self._makeMenu()

    def _makeMenu(self):
        """
        Creates the QClientMenuHeader with only a File menu.
        Does not associate the File menu with any slots.
        """
        # file menu
        self.fileMenu = QMenu("&File")
        self.addMenu(self.fileMenu)
        self.restart_action = QAction('&Restart')
        self.lockGUI_action = QAction('&Lock GUI')
        self.unlockGUI_action = QAction('&Unlock GUI')
        self.fileMenu.addAction(self.restart_action)
        self.fileMenu.addAction(self.lockGUI_action)
        self.fileMenu.addAction(self.unlockGUI_action)
        # config menu
        self.configMenu = QMenu("&Configuration")
        self.addMenu(self.configMenu)
        self.saveConfig_action = QAction('Save Configuration')
        self.loadConfig_action = QAction('Load Configuration')
        self.configMenu.addAction(self.saveConfig_action)
        self.configMenu.addAction(self.loadConfig_action)

    def addFile(self, client):
        """
        Associates the File menu with its corresponding slots.
        To be called by the client.
        Arguments:
            client: the GUIClient object that owns this QClientMenuHeader.
        """
        self.restart_action.triggered.connect(lambda: client._restart())
        self.lockGUI_action.triggered.connect(lambda: client._enableAllExceptHeader(False))
        self.unlockGUI_action.triggered.connect(lambda: client._enableAllExceptHeader(True))

    def addSerial(self, server):
        """
        Creates the Serial menu and associates actions
        with their corresponding slots.
        Arguments:
            server: the LabradServer object that we want to use.
        """
        # create and add serial sub-menu to main menu
        self.serialMenu = QMenu("&Serial")
        self.addMenu(self.serialMenu)
        # create and add serial menu actions
        self.node_action = QAction('Node')
        self.port_action = QAction('Port')
        self.connect_action = QAction('Connect')
        self.disconnect_action = QAction('Disconnect')
        self.clear_action = QAction('Clear Buffers')
        self.serialconnection_action = QAction('Serial Connection')
        self.serialMenu.addAction(self.node_action)
        self.serialMenu.addAction(self.port_action)
        self.serialMenu.addAction(self.connect_action)
        self.serialMenu.addAction(self.disconnect_action)
        self.serialMenu.addAction(self.clear_action)
        self.serialMenu.addAction(self.serialconnection_action)
        # connect actions to slots
        self.connect_action.triggered.connect(lambda action, _server=server: self._deviceSelect(_server))
        self.disconnect_action.triggered.connect(lambda action, _server=server: self._deviceClose(_server))
        self.clear_action.triggered.connect(lambda action, _server=server: self._deviceClear(_server))
        #self.restart_action.triggered.connect(lambda: client._restart())
        # todo: submenu for node, port, connection status
        # todo: can't change node/port if currently connected, grey out

    def addGPIB(self, server):
        """
        Creates the GPIB menu and associates actions
        with their corresponding slots.
        Arguments:
            server: the LabradServer object that we want to use.
        """
        self.gpibMenu = QMenu("&GPIB")
        self.addMenu(self.gpibMenu)
        self.select_action = QAction('Select Device')
        self.release_action = QAction('Release Device')
        self.lock_action = QAction('Lock Device')
        self.query_action = QAction('Query')
        self.write_action = QAction('Write')
        self.read_action = QAction('Read')
        self.gpibMenu.addAction(self.select_action)
        self.gpibMenu.addAction(self.release_action)
        self.gpibMenu.addAction(self.lock_action)
        self.gpibMenu.addAction(self.query_action)
        self.gpibMenu.addAction(self.write_action)
        self.gpibMenu.addAction(self.read_action)
        # todo: implement

    def addPolling(self, server):
        """
        Creates the Polling menu and associates actions
        with their corresponding slots.
        Arguments:
            server: the LabradServer object that we want to use.
        """
        # create and add polling sub-menu to main menu
        self.pollingMenu = QMenu("&Polling")
        self.addMenu(self.pollingMenu)
        # create and add polling menu actions
        self.pollstatus_action = QAction('Polling Active')
        self.pollstatus_action.setCheckable(True)
        self.pollrate_spinbox = QDoubleSpinBox()
        # poll rate
        self.pollrate_action = QWidgetAction()
        self.pollrate_spinbox.setMinimum(0.1)
        self.pollrate_spinbox.setMaximum(10)
        self.pollrate_spinbox.setSingleStep(0.1)
        self.pollrate_spinbox.setDecimals(1)
        self.pollrate_action.setDefaultWidget(self.pollrate_spinbox)
        # add actions
        self.pollingMenu.addAction(self.pollstatus_action)
        self.pollingMenu.addAction(self.pollrate_action)
        # connect actions to slots
        self.pollingMenu.triggered.connect(lambda action, _server=server: self._getPolling(_server))
        self.pollstatus_action.triggered.connect(lambda status, _server=server: self._setPollingStatus(_server, status))
        self.pollrate_spinbox.valueChanged.connect(lambda value, status=self.pollstatus_action.isChecked(), _server=server: print('yzde:', status, ',ll:', value))

    def addCommunication(self, server):
        """
        Creates the Communicate menu and associates actions
        with their corresponding slots.
        Arguments:
            server: the LabradServer object that we want to use.
        """
        # create and add Communicate sub-menu to main menu
        self.commMenu = QMenu("&Communicate")
        self.addMenu(self.commMenu)
        # create and add polling menu actions
        # self.pollstatus_action = QAction('Polling Active')
        # self.pollingMenu.addAction(self.pollstatus_action)
        # connect actions to slots
        # self.pollingMenu.triggered.connect(lambda action, _server=server: self._getPollingStatus(_server))


    # FUNCTIONS
    @inlineCallbacks
    def _deviceSelect(self, server):
        try:
            node, port = yield server.device_select()
            # todo: assign to self
            # todo: check if we have a device; if not, set node and port enabled
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _deviceClose(self, server):
        try:
            yield server.device_close()
            # todo: check if we have a device; if not, set node and port enabled
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _deviceClear(self, server):
        try:
            yield server.serial_flush()
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _getPolling(self, server):
        try:
            polling_status, polling_interval = yield server.polling()
            self.pollstatus_action.setChecked(polling_status)
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _setPollingStatus(self, server, status):
        try:
            polling_status, polling_interval = yield server.polling(status)
            self.pollstatus_action.setChecked(polling_status)
        except Exception as e:
            print(e)
