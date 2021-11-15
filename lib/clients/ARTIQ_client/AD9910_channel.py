import os
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.Widgets import TextChangingButton

class AD9910_channel_GUI(QFrame):
    """
    GUI for a single AD9910 DDS channel
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
        layout.addWidget(self.freq, 2, 0)
        layout.addWidget(self.ampl, 2, 1)
        layout.addWidget(self.att, 4, 0)
        layout.addWidget(self.rfswitch, 2, 2)
        self.setLayout(layout)


class AD9910_channels(QWidget):
    """
    Client for all DDS channels
    """
    name = "AD9910 Client"
    password = os.environ['LABRADPASSWORD']
    row_length = 4

    def __init__(self, reactor, channels, parent=None):
        super(AD9910_channels, self).__init__()
        self.reactor = reactor
        self.ad9910_list = channels
        self.ad9910_clients = {}
        self.connect()
        self.initializeGUI()

    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name=self.name, password=self.LABRADPASSWORD)
        self.artiq = self.cxn.ARTIQ_server

    def initializeGUI(self):
        layout = QGridLayout
        #layout widgets
        for i in range(len(self.ad9910_list)):
            # initialize GUIs for each channel
            channel_name = self.ad9910_list[i]
            channel_gui = AD9910_channel_GUI(channel_name)
            # layout channel GUI
            row = i % (self.row_length - 1)
            column = int(i / (self.row_length - 1))
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
            layout.addWidget(channel_gui, row, column)
        self.setLayout(layout)

    @inlineCallbacks
    def toggleSwitch(self, channel_name, status):
        yield self.artiq.toggleDDS(channel_name, status)

    @inlineCallbacks
    def setFrequency(self, channel_name, freq):
        yield self.artiq.set_DDS_frequency(channel_name, freq)

    @inlineCallbacks
    def setAmplitude(self, channel_name, ampl):
        yield self.artiq.set_DDS_amplitude(channel_name, ampl)

    @inlineCallbacks
    def setAttenuation(self, channel_name, att):
        yield self.artiq.set_DDS_attenuation(channel_name, att)




if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(AD9910_channel_GUI, 'AD9910 Channel')
