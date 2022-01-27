from PyQt5.QtGui import QFont
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QComboBox,\
    QHBoxLayout, QVBoxLayout, QPushButton

from random import randrange
from twisted.internet.defer import inlineCallbacks


class QSerialConnection(QFrame):
    def setupUi(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(330, 100)
        self.setWindowTitle("Device")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.widget = QWidget(self)
        self.widget.setGeometry(QRect(10, 10, 314, 80))
        self.verticalLayout_3 = QVBoxLayout(self.widget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.device_label = QLabel(self.widget)
        self.device_label.setText("Device")
        self.device_label.setFont(QFont(shell_font, pointSize=18))
        self.device_label.setAlignment(Qt.AlignCenter)
        self.verticalLayout_3.addWidget(self.device_label)
        self.horizontalLayout = QHBoxLayout()
        self.node_layout = QVBoxLayout()
        self.node_label = QLabel(self.widget)
        self.node_label.setText("Node")
        self.node_layout.addWidget(self.node_label)
        self.node = QComboBox(self.widget)
        self.node_layout.addWidget(self.node)
        self.horizontalLayout.addLayout(self.node_layout)
        self.port_layout = QVBoxLayout()
        self.port_label = QLabel(self.widget)
        self.port_label.setText("Port")
        self.port_layout.addWidget(self.port_label)
        self.port = QComboBox(self.widget)
        self.port_layout.addWidget(self.port)
        self.horizontalLayout.addLayout(self.port_layout)
        self.connect_button = QPushButton(self.widget)
        self.connect_button.setText("Connect")
        self.horizontalLayout.addWidget(self.connect_button)
        self.disconnect_button = QPushButton(self.widget)
        self.disconnect_button.setText("Disconnect")
        self.horizontalLayout.addWidget(self.disconnect_button)
        self.verticalLayout_3.addLayout(self.horizontalLayout)


class SerialConnection_Client(QSerialConnection):

    name = 'SerialConnection Client'

    def __init__(self, reactor, server, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        self.server_name = server
        self.nodes = {}
        self.BASE_ID = randrange(3e5, 1e6)
        # initialization sequence
        self.gui.setupUi()
        d = self.connect()
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)

    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to pump servers
        and relevant labrad servers
        """
        # create labrad connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        # try to get servers
        try:
            self.manager = self.cxn.manager
            self.server = self.cxn[self.server_name]
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)
        # connect to server connect/disconnect signals
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get all serial servers and ports
        """
        # get all servers
        server_names = yield self.manager.servers()
        server_names = [server_tuple[1] for server_tuple in server_names]
        # find serial servers
        for server_name in server_names:
            if 'serial server' in server_name.lower():
                # connect to signal
                self.BASE_ID += 1
                serial_server = self.cxn[server_name]
                yield serial_server.signal__port_update(self.BASE_ID)
                yield serial_server.addListener(listener=self.updatePorts, source=None, ID=self.BASE_ID)
                # get ports
                ports_tmp = yield serial_server.list_serial_ports()
                self.nodes[server_name] = {'ID': self.BASE_ID, 'ports': ports_tmp.sort()}
        # add nodes and ports to GUI
        self.gui.node.addItems(list(self.nodes.keys()))
        # get current connection
        self.gui.node.setCurrentIndex(-1)
        self.gui.port.setCurrentIndex(-1)
        _node, _port = yield self.server.device_select()
        _node, _port = yield self.server.device_select()
        _node = _node.strip().lower() + ' Serial Server'
        if _node in self.nodes.keys():
            self.gui.device_label.setStyleSheet('background-color: lightgreen')
        else:
            self.gui.device_label.setStyleSheet('background-color: red')
        # if (_node in self.nodes.keys()) and (_port in self.nodes[_node]['ports']):
        #     node_index = self.gui.node.findText(_node)
        #     port_index = self.gui.port.findText(_port)
        #     self.gui.node.setCurrentIndex(node_index)
        #     self.gui.port.setCurrentIndex(port_index)
        # else:
        #     print(_node)
        #     self.gui.node.setCurrentIndex(-1)
        #     self.gui.port.setCurrentIndex(-1)

    def initializeGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        # setup name
        self.gui.device_label.setText(self.server_name)
        self.gui.setWindowTitle(self.server_name)
        # connect to signals
        self.gui.connect_button.clicked.connect(lambda: self.pressConnect())
        self.gui.disconnect_button.clicked.connect(lambda: self.pressDisconnect())
        self.gui.node.currentTextChanged.connect(lambda node_name: self.chooseNode(node_name))


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if 'serial server' in server_name.lower():
            print(server_name + ' connected.')
            serial_server = self.cxn[server_name]
            self.BASE_ID += 1
            # get ports and connect to signal
            ports_tmp = yield serial_server.list_serial_ports()
            yield serial_server.signal__port_update(self.BASE_ID)
            yield serial_server.addListener(listener=self.updatePorts, source=None, ID=self.BASE_ID)
            self.nodes[server_name] = {'ID': self.BASE_ID, 'ports': ports_tmp.sort()}
            # update ports on GUI
            self.gui.node.addItem(server_name)
        elif server_name == self.server_name:
            yield self.initData(self.cxn)
            print(server_name + ' reconnected, enabling widget.')
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.nodes.keys():
            print(server_name + ' disconnected.')
            del self.nodes[server_name]
            # update ports as necessary
            if self.gui.port.currentText() == server_name:
                self.gui.node.clear()
            self.gui.port.removeItem(server_name)
        elif server_name == self.server_name:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)

    def updatePorts(self, c, node_data):
        """
        Updates node ports when values are received from server.
        """
        server_name, port_list = node_data
        self.nodes[server_name] = port_list.sort()
        # update ports as necessary
        if self.gui.port.currentText() == server_name:
            self.gui.node.clear()
            self.gui.node.addItems(port_list)


    # SLOTS
    @inlineCallbacks
    def pressConnect(self):
        """
        Connect to the selected device.
        """
        node_text = self.gui.node.currentText()
        port_text = self.gui.port.currentText()
        try:
            yield self.server.device_select(node_text, port_text)
        except Exception as e:
            print(e)
            self.gui.device_label.setStyleSheet('background-color: red')
        else:
            self.gui.device_label.setStyleSheet('background-color: lightgreen')

    @inlineCallbacks
    def pressDisconnect(self):
        """
        Disconnect from the current device.
        """
        try:
            yield self.server.device_close()
        except Exception as e:
            print(e)
            pass
        self.gui.device_label.setStyleSheet('background-color: red')

    def chooseNode(self, node_name):
        """
        Update the list of ports upon change of node selection.
        """
        self.gui.port.clear()
        self.gui.port.addItems(list(self.nodes[node_name]['ports']))

    def closeEvent(self, event):
        if self.reactor.running:
            self.reactor.stop()
        self.cxn.disconnect()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI, runClient
    #runGUI(QSerialConnection)
    runClient(SerialConnection_Client, server='Lakeshore336 Server')