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
        self.calibrateswitch = QPushButton('Calibrate')
        self.lockswitch = TextChangingButton(("Lock", "Unlock"))

        #add widgets to layout
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(dac_label, 1, 0, 1, 1)
        layout.addWidget(gain_label, 1, 1, 1, 1)
        layout.addWidget(off_label, 1, 2, 1, 1)
        layout.addWidget(self.dac, 2, 0)
        layout.addWidget(self.gain, 2, 1)
        layout.addWidget(self.off, 2, 2)
        layout.addWidget(self.lockswitch, 3, 0)
        layout.addWidget(self.calibrateswitch, 3, 1)
        layout.addWidget(self.calibrateswitch, 3, 2)
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
        for i in range(len(self.ad5372_list)):
            # initialize GUIs for each channel
            channel_name = self.ad5372_list[i]
            channel_gui = AD5372_channel(channel_name)
            # layout channel GUI
            row = int(i / (self.row_length)) + 2
            column = i % (self.row_length)
            # connect signals to slots
            channel_gui.freq.valueChanged.connect(lambda chan=channel_name, freq=channel_gui.freq.value():
                                                  self.setFrequency(chan, freq))
            channel_gui.ampl.valueChanged.connect(lambda chan=channel_name, ampl=channel_gui.ampl.value():
                                                  self.setAmplitude(chan, ampl))
            channel_gui.att.valueChanged.connect(lambda chan=channel_name, att=channel_gui.att.value():
                                                 self.setAttenuation(chan, att))
            channel_gui.rfswitch.toggled.connect(lambda chan=channel_name, status=channel_gui.rfswitch.isChecked():
                                                 self.toggleSwitch())
            # add widget to client list and layout
            self.ad5372_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column, 1, 1)
            #print('row:' + str(row) + ', column: ' + str(column))
        self.setLayout(layout)

    #todo: run asynchronously
    def _parseDevices(self):
        """
        Parses device_db for relevant devices.
        """
        #create holding lists
        self.ad5372_clients = {}
        self.ad5372_list = []
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            if params['class'] == 'AD5372':
                self.ad5372_list.append(name)

    @inlineCallbacks
    def toggleSwitch(self, channel_name, status):
        yield self.artiq.toggle_DAC(channel_name, status)

    @inlineCallbacks
    def setFrequency(self, channel_name, freq):
        yield self.artiq.set_DAC_frequency(channel_name, freq)

    @inlineCallbacks
    def setAmplitude(self, channel_name, ampl):
        yield self.artiq.set_DAC_amplitude(channel_name, ampl)

    @inlineCallbacks
    def setAttenuation(self, channel_name, att):
        yield self.artiq.set_DAC_attenuation(channel_name, att)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    #run channel GUI
    from EGGS_labrad.lib.clients import runGUI
    runGUI(AD5372_channel, name='AD5372 Channel')

    #run DAC GUI
    # from EGGS_labrad.lib.clients import runClient
    # runClient(DAC_client)
