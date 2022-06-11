from twisted.internet.defer import inlineCallbacks
from PyQt5.QtWidgets import QMenuBar, QMenu, QAction, QWidgetAction, QDoubleSpinBox, QLabel, QWidget, QVBoxLayout, QFrame


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
        self.saveConfig_action = QAction('&Save Configuration')
        self.loadConfig_action = QAction('&Load Configuration')
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
        self.node_menu = QMenu('Node')
        self.port_menu = QMenu('Port')
        self.connect_action = QAction('Connect')
        self.disconnect_action = QAction('Disconnect')
        self.clear_action = QAction('Clear Buffers')
        self.serialconnection_action = QAction('Serial Connection')
        self.serialMenu.addMenu(self.node_menu)
        self.serialMenu.addMenu(self.port_menu)
        self.serialMenu.addAction(self.connect_action)
        self.serialMenu.addAction(self.disconnect_action)
        self.serialMenu.addAction(self.clear_action)
        self.serialMenu.addAction(self.serialconnection_action)
        # connect actions to slots
        self.serialMenu.triggered.connect(lambda action, _server=server: self._getDevice(_server))
        self.node_menu.triggered.connect(lambda action, _server=server: self._getPolling(_server))
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
        self.deselect_action = QAction('Deselect Device')
        #self.lock_action = QAction('Lock Device')
        self.gpibMenu.addAction(self.select_action)
        self.gpibMenu.addAction(self.release_action)
        #self.gpibMenu.addAction(self.lock_action)
        # connect actions to slots
        self.select_action.triggered.connect(lambda action, _server=server: self._gpibSelect(_server))
        self.deselect_action.triggered.connect(lambda action, _server=server: self._gpibDeselect(_server))
        #self.lock_action.triggered.connect(lambda action, _server=server: self._gpibLock(_server))

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
        self.pollrate_action = QWidgetAction(self.pollingMenu)
        pollrate_widget = QFrame()
        pollrate_widget.setFrameStyle(0x0001 | 0x0010)
        pollrate_widget_layout = QVBoxLayout(pollrate_widget)
        pollrate_label = QLabel("Polling Interval (s)")
        self.pollrate_spinbox.setRange(0.1, 10)
        self.pollrate_spinbox.setSingleStep(0.1)
        self.pollrate_spinbox.setDecimals(1)
        self.pollrate_spinbox.setKeyboardTracking(False)
        pollrate_widget_layout.addWidget(pollrate_label)
        pollrate_widget_layout.addWidget(self.pollrate_spinbox)
        self.pollrate_action.setDefaultWidget(pollrate_widget)
        # add actions
        self.pollingMenu.addAction(self.pollstatus_action)
        self.pollingMenu.addAction(self.pollrate_action)
        # connect actions to slots
        self.pollingMenu.triggered.connect(lambda action, _server=server: self._getPolling(_server))
        self.pollstatus_action.triggered.connect(lambda status, _server=server: self._setPollingStatus(_server, status))
        self.pollrate_spinbox.valueChanged.connect(lambda value, _server=server: self._setPollingInterval(_server, value))
        # get initial state
        self._getPolling(server)

    def addCommunication(self, server):
        """
        Creates the Communication menu and associates actions
        with their corresponding slots.
        Arguments:
            server: the LabradServer object that we want to use.
        """
        # create and add communication sub-menu to main menu
        self.commMenu = QMenu("&Communication")
        self.addMenu(self.commMenu)
        # create and add communication menu actions
        self.query_action = QAction('Query')
        self.write_action = QAction('Write')
        self.read_action = QAction('Read')
        self.commMenu.addAction(self.query_action)# dialog box with input and buffer
        self.commMenu.addAction(self.write_action) #dialog box with input
        self.commMenu.addAction(self.read_action) # dialog box
        # connect actions to slots
        # self.pollingMenu.triggered.connect(lambda action, _server=server: self._getPollingStatus(_server))
        # todo: open up dialog box that works these functions


    """
    SLOTS
    """
    # SERIAL
    @inlineCallbacks
    def _getDevice(self, server):
        try:
            node, port = yield server.device_info()
            if node == '':
                self.node_menu.setEnabled(False)
                self.port_menu.setEnabled(False)
        except Exception as e:
            print(e)

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
    def _serialNodes(self, server):
        try:
            # todo: get serial server and get all ports
        except Exception as e:
            print(e)

    # GPIB
    @inlineCallbacks
    def _gpibSelect(self, server):
        try:
            yield server.select_device()
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _gpibDeselect(self, server):
        try:
            yield server.deselect_device()
        except Exception as e:
            print(e)

    # POLLING
    @inlineCallbacks
    def _getPolling(self, server):
        try:
            polling_status, polling_interval = yield server.polling()
            self.pollstatus_action.setChecked(polling_status)
            self.pollrate_spinbox.setValue(polling_interval)
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _setPollingStatus(self, server, status):
        try:
            interval = self.pollrate_spinbox.value()
            polling_status, polling_interval = yield server.polling(status, interval)
            self.pollstatus_action.setChecked(polling_status)
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _setPollingInterval(self, server, interval):
        try:
            status_tmp = self.pollstatus_action.isChecked()
            polling_status, polling_interval = yield server.polling(status_tmp, interval)
        except Exception as e:
            print(e)
