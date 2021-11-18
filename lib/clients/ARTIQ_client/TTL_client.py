import os
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.Widgets import TextChangingButton

class TTL_channel(QFrame):
    """
    GUI for a single TTL channel
    """
    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(name)

    def makeLayout(self, title):
        layout = QGridLayout()
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 3)

        self.toggle = TextChangingButton(("On", "Off"))
        layout.addWidget(self.toggle, 1, 1)
        self.setLayout(layout)


class TTL_client(QWidget):
    """
    Client for all TTL channels
    """
    name = "ARTIQ TTL Client"
    password = os.environ['LABRADPASSWORD']
    row_length = 4

    def __init__(self, reactor, channels, parent=None):
        super(TTL_client, self).__init__()
        self.reactor = reactor
        self.ttl_list = channels
        self.ttl_clients = {}
        self.connect()
        self.initializeGUI()

    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name=self.name, password=self.LABRADPASSWORD)
        self.artiq = self.cxn.registry

    def initializeGUI(self):
        layout = QGridLayout()
        #set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 4)
        #layout widgets
        for i in range(len(self.ttl_list)):
            # initialize GUIs for each channel
            channel_name = self.ttl_list[i]
            channel_gui = TTL_channel(channel_name)
            # layout channel GUI
            row = int(i / (self.row_length)) + 2
            column = i % (self.row_length)
            # connect signals to slots
            channel_gui.toggle.toggled.connect(lambda chan=channel_name, status=channel_gui.toggle.isChecked():
                                                 self.toggleSwitch())
            # add widget to client list and layout
            self.ttl_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column, 1, 1)
            print('row:' + str(row) + ', column: ' + str(column))
        self.setLayout(layout)

    @inlineCallbacks
    def toggleSwitch(self, channel_name, status):
        yield self.artiq.set_TTL(channel_name, status)

    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == "__main__":
    #run channel GUI
    # from EGGS_labrad.lib.clients import runGUI
    # runGUI(TTL_channel, name='TTL Channel')
    #run TTL GUI
    from EGGS_labrad.lib.servers.ARTIQ.device_db import device_db
    ttl_list = []
    for device_name, device_params in device_db.items():
        try:
            if device_params['class'] == 'TTLOut':
                ttl_list.append(device_name)
        except KeyError:
            continue
    from EGGS_labrad.lib.clients import runClient
    runClient(TTL_client, channels=ttl_list)
