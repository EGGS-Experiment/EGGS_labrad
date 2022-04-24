from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.Widgets import TextChangingButton


class AD9910_channel(QFrame):
    """
    GUI for a single AD9910 DDS channel.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(name)
        self.setMaximumSize(200, 100)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        title.setAlignment(Qt.AlignCenter)
        freqlabel = QLabel('Frequency (MHz)')
        powerlabel = QLabel('Amplitude (V)')
        attlabel = QLabel('Attenuation (dBm)')

        # editable fields
        self.freq = QDoubleSpinBox()
        self.freq.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.freq.setDecimals(3)
        self.freq.setSingleStep(0.001)
        self.freq.setRange(0.0, 400.0)
        self.freq.setKeyboardTracking(False)
        self.ampl = QDoubleSpinBox()
        self.ampl.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.ampl.setDecimals(3)
        self.ampl.setSingleStep(0.1)
        self.ampl.setRange(-145.0, 30.0)
        self.ampl.setKeyboardTracking(False)
        self.att = QDoubleSpinBox()
        self.att.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.att.setDecimals(3)
        self.att.setSingleStep(0.1)
        self.att.setRange(-145.0, 30.0)
        self.att.setKeyboardTracking(False)
        self.resetswitch = QPushButton('Initialize')
        self.rfswitch = TextChangingButton(("On", "Off"))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

        # add widgets to layout
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(freqlabel, 1, 0, 1, 1)
        layout.addWidget(powerlabel, 1, 1, 1, 1)
        layout.addWidget(attlabel, 1, 2, 1, 1)
        layout.addWidget(self.freq, 2, 0)
        layout.addWidget(self.ampl, 2, 1)
        layout.addWidget(self.att, 2, 2)
        layout.addWidget(self.resetswitch, 3, 0)
        layout.addWidget(self.rfswitch, 3, 1)
        layout.addWidget(self.lockswitch, 3, 2)

    def lock(self, status):
        self.freq.setEnabled(status)
        self.ampl.setEnabled(status)
        self.att.setEnabled(status)
        self.rfswitch.setEnabled(status)


class AD9910_client(GUIClient):
    """
    Client for a single DDS channel.
    """

    name = "AD9910 Client"
    servers = {'aq': 'ARTIQ Server'}
    dds_name = 'urukul0_ch0'

    # def __init__(self, dds_name):
    #     self.dds_name = dds_name
    #     super().__init__()

    def getgui(self):
        if self.gui is None:
            self.gui = AD9910_channel(self.dds_name)
        return self.gui

    #@inlineCallbacks
    def initClient(self):
        pass

    #@inlineCallbacks
    def initData(self):
        pass

    def initGUI(self):
        self.gui.freq.valueChanged.connect(lambda freq, chan=self.dds_name: self.artiq.dds_frequency(chan, freq))
        self.gui.ampl.valueChanged.connect(lambda ampl, chan=self.dds_name: self.artiq.dds_amplitude(chan, ampl))
        self.gui.att.valueChanged.connect(lambda att, chan=self.dds_name: self.artiq.dds_attenuation(chan, att, 'v'))
        self.gui.rfswitch.toggled.connect(lambda status, chan=self.dds_name: self.artiq.dds_toggle(chan, status))
        self.gui.lock(False)


if __name__ == "__main__":
    # run channel GUI
    # from EGGS_labrad.clients import runGUI
    # runGUI(AD9910_channel, name='AD9910 Channel')

    # run AD9910 Client
    from EGGS_labrad.clients import runClient
    runClient(AD9910_client)
