from os import environ, path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QComboBox,\
    QHBoxLayout, QVBoxLayout, QPushButton, QMenuBar, QMenuBar, QMenu,\
    QToolBar, QMessageBox, QAction


from twisted.internet.defer import inlineCallbacks


class QClientHeader(QFrame):
    """
    A basic client header that shows the client name and has
    a restart button to allow restarts.
    """

    def __init__(self, name, serial=False, polling=False):
        super().__init__()
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self._makeHeader()
        if serial == True:
            self._makeSerial()
        if polling == True:
            self._makePolling()

    def _makeHeader(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QHBoxLayout(self)
        # title
        self.title = QLabel(self.name)
        self.title.setFont(QFont(shell_font, pointSize=15))
        self.title.setAlignment(Qt.AlignCenter)
        # restart button
        self.restartbutton = QPushButton()
        # set restart button icon
        path_root = environ['EGGS_LABRAD_ROOT']
        icon_path = path.join(path_root, 'EGGS_labrad\\clients\\Widgets\\refresh.png')
        self.restartbutton.setIcon(QIcon(icon_path))
        # lay out
        layout.addWidget(self.title)
        layout.addWidget(self.restartbutton)
        # set fixed size
        self.setMinimumSize(1.8 * self.title.sizeHint())

    def _makeSerial(self):
        pass

    def _makePolling(self):
        pass


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
        """
        self.restart_action.triggered.connect(lambda: client._restart())
        #self.lockGUI_action.triggered.connect(lambda: client._restart())
        #self.unlockGUI_action.triggered.connect(lambda: self.restart())
        pass

    #@inlineCallbacks
    def addSerial(self, server):
        """
        Creates the Serial menu and associates actions
        with their corresponding slots.
        """
        # serial: device info, node, port, connect/disconnect
        # create and add serial sub-menu to main menu
        self.serialMenu = QMenu("&Serial")
        self.addMenu(self.serialMenu)
        # create and add serial menu actions
        self.node_action = QAction('Node')
        self.port_action = QAction('Port')
        self.connect_action = QAction('Connect')
        self.disconnect_action = QAction('Disconnect')
        self.clear_action = QAction('Clear Buffers')
        self.serialMenu.addAction(self.node_action)
        self.serialMenu.addAction(self.port_action)
        self.serialMenu.addAction(self.connect_action)
        self.serialMenu.addAction(self.disconnect_action)
        self.serialMenu.addAction(self.clear_action)
        # connect actions to slots
        self.connect_action.triggered.connect(lambda status, _server=server: self._deviceselect(_server))
        self.disconnect_action.triggered.connect(lambda status, _server=server: self._deviceclose(_server))
        #self.restart_action.triggered.connect(lambda: client._restart())
        #self.restart_action.triggered.connect(lambda: client._restart())
        #self.restart_action.triggered.connect(lambda: client._restart())
        # todo: can't change node/port if currently connected
        # todo: baud rate, stop bits
        # todo: status?

    @inlineCallbacks
    def _deviceselect(self, server):
        try:
            node, port = yield server.device_select()
            # todo: assign to self
        except Exception as e:
            print(e)

    @inlineCallbacks
    def _deviceclose(self, server):
        try:
            yield server.device_close()
        except Exception as e:
            print(e)

    def addGPIB(self, server):
        """
        Creates the GPIB menu and associates actions
        with their corresponding slots.
        """
        # serial: device info, node, port, connect/disconnect
        self.serialMenu = QMenu("&GPIB")
        self.addMenu(self.serialMenu)
        self.select_action = QAction('Select Device')
        self.release_action = QAction('Release Device')
        self.lock_action = QAction('Lock Device')
        self.query_action = QAction('Query')
        self.write_action = QAction('Write')
        self.read_action = QAction('Read')
        self.serialMenu.addAction(self.select_action)
        self.serialMenu.addAction(self.release_action)
        self.serialMenu.addAction(self.lock_action)
        self.serialMenu.addAction(self.query_action)
        self.serialMenu.addAction(self.write_action)
        self.serialMenu.addAction(self.read_action)

    def addPolling(self, server):
        """
        Creates the Polling menu and associates actions
        with their corresponding slots.
        """
        # polling: poll time, poll status
        # create and add polling sub-menu to main menu
        self.pollingMenu = QMenu("&Polling")
        self.addMenu(self.pollingMenu)
        # create and add serial menu actions
        self.pollstatus_action = QAction('Status')
        self.pollrate_action = QAction('Rate')
        self.pollingMenu.addAction(self.pollstatus_action)
        self.pollingMenu.addAction(self.pollrate_action)
        # connect actions to slots
        #self.connect_action.triggered.connect(lambda status, _server=server: self._deviceselect(_server))
