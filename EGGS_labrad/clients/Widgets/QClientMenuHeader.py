from twisted.internet.defer import inlineCallbacks
from PyQt5.QtWidgets import QMenuBar, QMenu, QAction, QWidgetAction, QDoubleSpinBox, QLabel, QWidget, QVBoxLayout, QFrame


class QClientMenuHeader(QMenuBar):
    """
    A client menu header that breaks out core server functions.
    Designed to be initialized by a GUIClient.
    """

    def __init__(self, cxn=None, parent=None):
        super(QClientMenuHeader, self).__init__(parent)
        self.cxn = cxn
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
        self.node_menu = QMenu('Port')
        self.connect_action = QAction('Connect Default')
        self.disconnect_action = QAction('Disconnect')
        self.clear_action = QAction('Clear Buffers')
        self.serialconnection_action = QAction('Serial Connection')
        self.serialMenu.addMenu(self.node_menu)
        self.serialMenu.addAction(self.connect_action)
        self.serialMenu.addAction(self.disconnect_action)
        self.serialMenu.addAction(self.clear_action)
        self.serialMenu.addAction(self.serialconnection_action)
        # connect actions to slots
        self.serialMenu.aboutToShow.connect(lambda _server=server: self._getSerialDevice(_server))
        self.node_menu.aboutToShow.connect(lambda _server=server: self._getNodes(_server))
        self.connect_action.triggered.connect(lambda action, _server=server: self._deviceSelect(_server))
        self.disconnect_action.triggered.connect(lambda action, _server=server: self._deviceClose(_server))
        self.clear_action.triggered.connect(lambda action, _server=server: self._deviceClear(_server))

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
        self.gpibMenu.addAction(self.deselect_action)
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
        self.pollingMenu.aboutToShow.connect(lambda _server=server: self._getPolling(_server))
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
        self.query_action = QAction('&Query')
        self.write_action = QAction('&Write')
        self.read_action = QAction('&Read')
        self.commMenu.addAction(self.query_action)# dialog box with input and buffer
        self.commMenu.addAction(self.write_action) #dialog box with input
        self.commMenu.addAction(self.read_action) # dialog box
        # connect actions to slots
        self.query_action.triggered.connect(lambda action, _server=server: self._queryDialog(_server))
        self.write_action.triggered.connect(lambda action, _server=server: self._writeDialog(_server))
        self.read_action.triggered.connect(lambda action, _server=server: self._readDialog(_server))


    """
    SLOTS
    """
    # SERIAL
    @inlineCallbacks
    def _getSerialDevice(self, server):
        try:
            node, port = yield server.device_info()
            if node == '':
                self.node_menu.setEnabled(True)
                self.connect_action.setEnabled(True)
            else:
                self.node_menu.setEnabled(False)
                self.connect_action.setEnabled(False)
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _getNodes(self, server):
        try:
            # clear submenu
            self.node_menu.clear()
            # get serial servers
            servers = yield self.cxn.manager.servers()
            serial_servers = [server_name for _, server_name in servers if "serial server" in server_name.lower()]
            # create holding dictionary of nodes and ports
            for server_name in serial_servers:
                # add node submenu
                node_name = server_name.split(" ")[0]
                serial_server_menu = self.node_menu.addMenu(node_name)
                # get ports
                ports = yield self.cxn.servers[server_name].list_serial_ports()
                # create port actions
                for port_name in sorted(ports):
                    port_connect_action = serial_server_menu.addAction(port_name)
                    port_connect_action.triggered.connect(lambda action, _server=server, _node=node_name, _port=port_name:
                                                          _server.device_select(_node, _port))
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _deviceSelect(self, server):
        try:
            yield server.device_select()
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _deviceClose(self, server):
        try:
            yield server.device_close()
            # todo: check if we have a device; if not, set node and port enabled
        except Exception as e:
            print('scde')
            print(e)

    @inlineCallbacks
    def _deviceClear(self, server):
        try:
            yield server.serial_flush()
        except Exception as e:
            print(e)


    # GPIB
    @inlineCallbacks
    def _gpibSelect(self, server):
        try:
            # todo: log
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

    # COMMUNICATION
    @inlineCallbacks
    def _queryDialog(self, server):
        try:
            # todo: open dialog box that queries
            pass
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _writeDialog(self, server):
        try:
            # todo: open dialog box that write
            pass
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _readDialog(self, server):
        try:
            # todo: open dialog box that reads
            pass
        except Exception as e:
            print(e)
