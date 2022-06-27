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
        # create file menu
        file_menu = ("fileMenu", "&File")
        file_actions = {
            "restart_action": "&Restart",
            "lockGUI_action": "&Lock GUI",
            "unlockGUI_action": "&Unlock GUI",
            "serialconnection_action": "Serial Connection"
        }
        self._createMenu(file_menu, action_dict=file_actions)

        # create config menu
        config_menu = ("configMenu", "&Configuration")
        config_actions = {
            "saveConfig_action": "&Save Configuration",
            "loadConfig_action": "&Load Configuration"
        }
        self._createMenu(config_menu, action_dict=config_actions)

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
        menu_names = ("serialMenu", "&Serial")
        submenu_names = {"node_menu": "Port"}
        action_names = {
            "connect_action": "Connect Default",
            "disconnect_action": "Disconnect",
            "clear_action": "Clear Buffers",
            "serialconnection_action": "Serial Connection"
        }
        self._createMenu(menu_names, submenu_names, action_names)

        # connect actions to slots
        self.serialMenu.aboutToShow.connect(lambda _server=server: self._getSerialDevice(_server))
        self.node_menu.aboutToShow.connect(lambda _server=server: self._getNodes(_server))
        self.connect_action.triggered.connect(lambda action, _server=server: server.device_select())
        self.disconnect_action.triggered.connect(lambda action, _server=server: server.device_close())
        self.clear_action.triggered.connect(lambda action, _server=server:  server.serial_flush())

    def addGPIB(self, server):
        """
        Creates the GPIB menu and associates actions
            with their corresponding slots.
        Arguments:
            server: the LabradServer object that we want to use.
        """
        menu_names = ("gpibMenu", "&GPIB")
        action_names = {
            "select_action": "Select Device",
            "deselect_action": "Deselect Device"
            #"lock_action": "Lock Device"
        }
        self._createMenu(menu_names, action_dict=action_names)

        # connect actions to slots
        self.select_action.triggered.connect(lambda action, _server=server: server.select_device())
        self.deselect_action.triggered.connect(lambda action, _server=server: server.deselect_device())
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
        menu_names = ("commMenu", "&Communication")
        action_names = {
            "query_action": "&Query",
            "write_action": "&Write",
            "read_action": "&Read"
        }
        self._createMenu(menu_names, action_dict=action_names)

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


    # POLLING
    @inlineCallbacks
    def _getPolling(self, server):
        try:
            polling_status, polling_interval = yield server.polling()
            # set polling status
            self.pollstatus_action.setChecked(polling_status)
            if self.pollstatus_action.isChecked():
                self.pollstatus_action.setText("Polling Active")
            else:
                self.pollstatus_action.setText("Polling Inactive")
            # set polling rate
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
            yield server.polling(status_tmp, interval)
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


    # HELPERS
    def _createMenu(self, menu, submenu_dict={}, action_dict={}):
        """
        Creates actions and adds them to the given menu.
        Arguments:
            menu: a tuple of (menu_reference: menu_name)
            submenu_dict: a dictionary of {submenu_reference: submenu_name}
            action_dict: a dictionary of {action_reference: action_name}
        """
        # create and add menu
        menu_obj = QMenu(menu[1])
        setattr(self, menu[0], menu_obj)
        self.addMenu(menu_obj)

        # create and add submenus to menu
        for submenu_ref, submenu_name in submenu_dict.items():
            submenu_obj = QMenu(submenu_name)
            setattr(self, submenu_ref, submenu_obj)
            menu_obj.addMenu(submenu_obj)

        # create and add actions to menu
        for action_ref, action_name in action_dict.items():
            action_obj = QAction(action_name)
            setattr(self, action_ref, action_obj)
            menu_obj.addAction(action_obj)
