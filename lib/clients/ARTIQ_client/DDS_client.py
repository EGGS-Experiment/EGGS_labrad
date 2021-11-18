import os
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.Widgets import TextChangingButton
from EGGS_labrad.lib.servers.ARTIQ.device_db import device_db

class AD9910_channel(QFrame):
    """
    GUI for a single AD9910 DDS channel.
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
        freqlabel = QLabel('Frequency (MHz)')
        powerlabel = QLabel('Amplitude (V)')
        attlabel = QLabel('Attenuation (dBm)')
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(freqlabel, 1, 0, 1, 1)
        layout.addWidget(powerlabel, 1, 1, 1, 1)
        layout.addWidget(attlabel, 3, 0, 1, 1)

        # editable fields
        self.freq = QDoubleSpinBox()
        self.freq.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.freq.setDecimals(3)
        self.freq.setSingleStep(0.1)
        self.freq.setRange(10.0, 250.0)
        self.freq.setKeyboardTracking(False)
        self.ampl = QDoubleSpinBox()
        self.ampl.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.ampl.setDecimals(3)
        self.ampl.setSingleStep(0.1)
        self.ampl.setRange(-145.0, 30.0)
        self.ampl.setKeyboardTracking(False)
        self.att = QDoubleSpinBox()
        self.att.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.att.setDecimals(3)
        self.att.setSingleStep(0.1)
        self.att.setRange(-145.0, 30.0)
        self.att.setKeyboardTracking(False)
        self.rfswitch = TextChangingButton(("On", "Off"))
        self.lockswitch = TextChangingButton(("Lock", "Unlock"))

        #add widgets to layout
        layout.addWidget(self.freq, 2, 0)
        layout.addWidget(self.ampl, 2, 1)
        layout.addWidget(self.att, 4, 0)
        layout.addWidget(self.rfswitch, 2, 2)
        #layout.addWidget(self.rfswitch, 2, 2)
        self.setLayout(layout)


class DDS_client(QWidget):
    """
    Client for all DDS channels.
    """
    name = "ARTIQ DDS Client"
    row_length = 6

    def __init__(self, reactor, cxn=None, parent=None):
        super(DDS_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.device_db = device_db
        self._parseDevices()
        self.ad9910_clients = {}
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
        for i in range(len(self.ad9910_list)):
            # initialize GUIs for each channel
            channel_name = self.ad9910_list[i]
            channel_gui = AD9910_channel(channel_name)
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
            self.ad9910_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column, 1, 1)
            #print('row:' + str(row) + ', column: ' + str(column))
        self.setLayout(layout)

    #todo: run asynchronously
    def _parseDevices(self):
        """
        Parses device_db for relevant devices.
        """
        #create holding lists
        self.ad9910_list = []
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            if params['class'] == 'AD9910':
                self.ad9910_list.append(name)

    @inlineCallbacks
    def toggleSwitch(self, channel_name, status):
        yield self.artiq.toggle_DDS(channel_name, status)

    @inlineCallbacks
    def setFrequency(self, channel_name, freq):
        yield self.artiq.set_DDS_frequency(channel_name, freq)

    @inlineCallbacks
    def setAmplitude(self, channel_name, ampl):
        yield self.artiq.set_DDS_amplitude(channel_name, ampl)

    @inlineCallbacks
    def setAttenuation(self, channel_name, att):
        yield self.artiq.set_DDS_attenuation(channel_name, att)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    #run channel GUI
    # from EGGS_labrad.lib.clients import runGUI
    # runGUI(AD9910_channel, name='AD9910 Channel')

    #run DDS GUI
    from EGGS_labrad.lib.clients import runClient
    runClient(DDS_client)
