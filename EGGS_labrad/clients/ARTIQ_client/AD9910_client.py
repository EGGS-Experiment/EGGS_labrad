from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks
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
        self.initializeGUI()

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
        self.freq.setSingleStep(0.1)
        self.freq.setRange(10.0, 250.0)
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
        self.lockswitch.setChecked(True)

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

    def initializeGUI(self):
        # connect signal to slot
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))
        # set startup value
        # self.lockswitch.toggle()

    def lock(self, status):
        self.rfswitch.setEnabled(status)


class AD9910_client(GUIClient):
    """
    Client for a single DDS channel.
    """

    name = "AD9910 Client"

    def __init__(self, reactor, cxn=None, parent=None):
        super(AD9910_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.ad9910_clients = {}
        # start connections
        d = self.connect()
        d.addCallback(self.getDevices)
        d.addCallback(self.initializeGUI)

    @inlineCallbacks
    def connect(self):
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        return self.cxn

    @inlineCallbacks
    def getDevices(self, cxn):
        """
        Get devices from ARTIQ server and organize them.
        """
        # get artiq server and dds list
        try:
            self.artiq = yield self.cxn.artiq_server
            ad9910_list = yield self.artiq.dds_list()
        except Exception as e:
            print(e)
            raise

        # assign ad9910 channels to urukuls
        self.urukul_list = {}
        for device_name in ad9910_list:
            urukul_name = device_name.split('_')[0]
            if urukul_name not in self.urukul_list:
                self.urukul_list[urukul_name] = []
            self.urukul_list[urukul_name].append(device_name)
        return self.cxn

    def initializeGUI(self, cxn):
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # layout widgets
        keys_tmp = list(self.urukul_list.keys())
        for i in range(len(keys_tmp)):
            urukul_name = keys_tmp[i]
            ad9910_list = self.urukul_list[urukul_name]
            urukul_group = self._makeUrukulGroup(urukul_name, ad9910_list)
            layout.addWidget(urukul_group, 2 + i, 0, 1, self.row_length)

    def _makeUrukulGroup(self, urukul_name, ad9910_list):
        """
        Creates a group of Urukul channels as a widget.
        """
        # create widget
        urukul_group = QFrame()
        urukul_group.setFrameStyle(0x0001 | 0x0010)
        urukul_group.setLineWidth(2)
        layout = QGridLayout(urukul_group)
        # set title
        title = QLabel(urukul_name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # layout individual ad9910 channels
        for i in range(len(ad9910_list)):
            # initialize GUIs for each channel
            channel_name = ad9910_list[i]
            channel_gui = AD9910_channel(channel_name)
            # layout channel GUI
            row = int(i / self.row_length) + 2
            column = i % self.row_length
            # connect signals to slots
            channel_gui.freq.valueChanged.connect(lambda freq, chan=channel_name: self.artiq.dds_frequency(chan, freq))
            channel_gui.ampl.valueChanged.connect(lambda ampl, chan=channel_name: self.artiq.dds_amplitude(chan, ampl))
            channel_gui.att.valueChanged.connect(lambda att, chan=channel_name: self.artiq.dds_attenuation(chan, att, 'v'))
            channel_gui.rfswitch.toggled.connect(lambda status, chan=channel_name: self.artiq.dds_toggle(chan, status))
            # add widget to client list and layout
            self.ad9910_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
            # print(name + ' - row:' + str(row) + ', column: ' + str(column))
        return urukul_group

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    # run channel GUI
    # from EGGS_labrad.clients import runGUI
    # runGUI(AD9910_channel, name='AD9910 Channel')

    # run AD9910 Client
    from EGGS_labrad.clients import runClient
    runClient(AD9910_client)