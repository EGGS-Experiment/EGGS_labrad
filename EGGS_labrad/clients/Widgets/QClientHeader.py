from os import environ, path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QComboBox,\
    QHBoxLayout, QVBoxLayout, QPushButton, QMenuBar, QMenuBar, QMenu,\
    QToolBar, QMessageBox, QAction

# todo: join the two
class QClientHeader(QFrame):
    """
    A basic client header that shows the client name and has
    a restart button to allow restarts.
    Designed to be called by a GUIClient class for
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
    A basic client header that shows the client name and has
    a restart button to allow restarts.
    Designed to be called by a GUIClient class for
    """

    def __init__(self, serial=False, polling=False, parent=None):
        super().__init__(parent)
        self.makeMenu()
        if serial: self.addSerial()
        if polling: self.addPolling()

    def makeMenu(self):
        self.fileMenu = QMenu("&File")
        self.addMenu(self.fileMenu)
        self.restart_action = QAction('Restart')
        #self.restart_action.triggered.connect(lambda: self.restart())
        self.fileMenu.addAction(self.restart_action)

    def addSerial(self):
        # serial: device info, node, port, connect/disconnect
        self.serialMenu = QMenu("&Serial")
        self.addMenu(self.serialMenu)
        self.node_action = QAction('Node')
        self.port_action = QAction('Port')
        self.connect_action = QAction('Connect')
        self.disconnect_action = QAction('Disconnect')
        #self.restart_action.triggered.connect(lambda: self.restart())
        self.serialMenu.addAction(self.node_action)
        self.serialMenu.addAction(self.port_action)
        self.serialMenu.addAction(self.connect_action)
        self.serialMenu.addAction(self.disconnect_action)

    def addPolling(self):
        # polling: poll time, poll status
        self.pollingMenu = QMenu("&Serial")
        self.addMenu(self.pollingMenu)
        self.pollstatus_action = QAction('Polling Status')
        self.pollrate_action = QAction('Polling Rate')
        self.serialMenu.addAction(self.pollstatus_action)
        self.serialMenu.addAction(self.pollrate_action)
