from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFrame


class QSerialConnection(QFrame):

    def setupUi(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(330, 100)
        self.setWindowTitle("Device")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.widget = QtWidgets.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(10, 10, 314, 80))
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.device_label = QtWidgets.QLabel(self.widget)
        self.device_label.setText("Device")
        self.device_label.setFont(QtGui.QFont(shell_font, pointSize=18))
        self.device_label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout_3.addWidget(self.device_label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.node_layout = QtWidgets.QVBoxLayout()
        self.node_label = QtWidgets.QLabel(self.widget)
        self.node_label.setText("Node")
        self.node_layout.addWidget(self.node_label)
        self.node = QtWidgets.QComboBox(self.widget)
        self.node_layout.addWidget(self.node)
        self.horizontalLayout.addLayout(self.node_layout)
        self.port_layout = QtWidgets.QVBoxLayout()
        self.port_label = QtWidgets.QLabel(self.widget)
        self.port_label.setText("Port")
        self.port_layout.addWidget(self.port_label)
        self.port = QtWidgets.QComboBox(self.widget)
        self.port_layout.addWidget(self.port)
        self.horizontalLayout.addLayout(self.port_layout)
        self.connect = QtWidgets.QPushButton(self.widget)
        self.connect.setText("Connect")
        self.horizontalLayout.addWidget(self.connect)
        self.disconnect = QtWidgets.QPushButton(self.widget)
        self.disconnect.setText("Disconnect")
        self.horizontalLayout.addWidget(self.disconnect)
        self.verticalLayout_3.addLayout(self.horizontalLayout)


class SerialConnection_Client(QSerialConnection):

    name = 'SerialConnection Client'

    PRESSUREID = 694321

    def __init__(self, reactor, server, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        self.server = server
        # initialization sequence
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
            # todo
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)

        # connect to signals
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)

        # start device polling
        poll_params = yield self.tt.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.tt.polling(True, 5.0)

        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        power_tmp = yield self.tt.toggle()
        self.gui.twistorr_power.setChecked(power_tmp)

    @inlineCallbacks
    def initializeGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        self.gui.twistorr_lockswitch.toggled.connect(lambda status: self.lock_twistorr(status))
        self.gui.twistorr_power.clicked.connect(lambda status: self.toggle_twistorr(status))
        self.gui.twistorr_record.toggled.connect(lambda status: self.record_pressure(status))


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            yield self.initData(self.cxn)
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)

    def updateEnergy(self, c, energy):
        """
        Updates GUI when values are received from server.
        """
        self.gui.power_display.setText(str(energy))


    # SLOTS
    def toggle_twistorr(self, status):
        """
        Sets pump power on or off.
        """
        print('set power: ' + str(status))

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(QSerialConnection)