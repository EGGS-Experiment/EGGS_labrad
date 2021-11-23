import os
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.Widgets import TextChangingButton
from EGGS_labrad.lib.servers.ARTIQ.device_db import device_db

class AD5372_channel(QFrame):
    """
    GUI for a single AD5372 DAC channel.
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
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        dac_label = QLabel('DAC (MHz)')
        gain_label = QLabel('Gain (V)')
        off_label = QLabel('Offset (dBm)')

        # editable fields
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(3)
        self.dac.setSingleStep(0.1)
        self.dac.setRange(10.0, 250.0)
        self.dac.setKeyboardTracking(False)
        self.gain = QDoubleSpinBox()
        self.gain.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.gain.setDecimals(3)
        self.gain.setSingleStep(0.1)
        self.gain.setRange(-145.0, 30.0)
        self.gain.setKeyboardTracking(False)
        self.off = QDoubleSpinBox()
        self.off.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.off.setDecimals(3)
        self.off.setSingleStep(0.1)
        self.off.setRange(-145.0, 30.0)
        self.off.setKeyboardTracking(False)

        # buttons
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.calibrateswitch = QPushButton('Calibrate')
        self.calibrateswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = TextChangingButton(('Locked', 'Unlocked'))

        # add widgets to layout
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(dac_label, 1, 0, 1, 1)
        layout.addWidget(gain_label, 1, 1, 1, 1)
        layout.addWidget(off_label, 1, 2, 1, 1)
        layout.addWidget(self.dac, 2, 0)
        layout.addWidget(self.gain, 2, 1)
        layout.addWidget(self.off, 2, 2)
        layout.addWidget(self.lockswitch, 3, 0)
        layout.addWidget(self.calibrateswitch, 3, 1)
        layout.addWidget(self.resetswitch, 3, 2)
        self.setLayout(layout)


class DAC_client(QWidget):
    """
    Client for all DAC channels.
    """
    name = "ARTIQ DAC Client"
    row_length = 6

    def __init__(self, reactor, cxn=None, parent=None):
        super(DAC_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.device_db = device_db
        self._parseDevices()
        self.connect()
        self.initializeGUI()

    @inlineCallbacks
    def connect(self):
        if not self.cxn:
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync('localhost', name=self.name)
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
            self.artiq = self.cxn.artiq_server
        except Exception as e:
            print(e)
            raise

    def initializeGUI(self):
        layout = QGridLayout()
        #set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 4)
        #layout widgets
        for i in range(len(self.zotino_list)):
            name = self.zotino_list[i]
            zotino_group = self._makeZotinoGroup(name)
            layout.addWidget(zotino_group, 2 + i, 0)
        self.setLayout(layout)

    def _makeZotinoGroup(self, name):
        """
        Creates a group of zotino channels as a widget.
        """
        # create widget
        zotino_group = QFrame()
        zotino_group.setFrameStyle(0x0001 | 0x0010)
        zotino_group.setLineWidth(2)
        layout = QGridLayout()
        # set title
        title = QLabel(name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # layout individual channels (32 per zotino)
        for i in range(32):
            # initialize GUIs for each channel
            channel_name = name + '_' + str(i)
            channel_gui = AD5372_channel(channel_name)
            # layout channel GUI
            row = int(i / self.row_length) + 2
            column = i % self.row_length
            # connect signals to slots
            channel_gui.dac.valueChanged.connect(lambda value, chan=channel_name:
                                                 self.setDAC(chan, value))
            channel_gui.gain.valueChanged.connect(lambda value, chan=channel_name:
                                                  self.setGain(chan, value))
            channel_gui.off.valueChanged.connect(lambda value, chan=channel_name:
                                                 self.setOffset(chan, value))
            channel_gui.calibrateswitch.clicked.connect(lambda: self.calibrate)
            channel_gui.resetswitch.clicked.connect(lambda: self.reset)
            channel_gui.lockswitch.clicked.connect(lambda status: self.lock(status))
            # add widget to client list and layout
            self.ad5372_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
            # print(name + ' - row:' + str(row) + ', column: ' + str(column))
        zotino_group.setLayout(layout)
        return zotino_group

    def _parseDevices(self):
        """
        Parses device_db for relevant devices.
        """
        #create holding lists
        self.zotino_list = []
        self.ad5372_clients = {}
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            if params['class'] == 'Zotino':
                self.zotino_list.append(name)

    @inlineCallbacks
    def setFrequency(self, channel_name, freq):
        yield self.artiq.set_DAC_frequency(channel_name, freq)

    @inlineCallbacks
    def setAmplitude(self, channel_name, ampl):
        yield self.artiq.set_DAC_amplitude(channel_name, ampl)

    @inlineCallbacks
    def setAttenuation(self, channel_name, att):
        yield self.artiq.set_DAC_attenuation(channel_name, att)

    def lock(self, status):
        """
        Locks DAC channel interface.
        """
        # invert since textchangingbutton is weird
        status = not status
        for channel in self.ad5372_clients.values():
            channel.setEnabled(status)

    def closeEvent(self, x):
        self.cxn.disconnect()
        self.reactor.stop()


if __name__ == "__main__":
    #run channel GUI
    # from EGGS_labrad.lib.clients import runGUI
    # runGUI(AD5372_channel, name='AD5372 Channel')

    #run DAC GUI
    from EGGS_labrad.lib.clients import runClient
    runClient(DAC_client)
