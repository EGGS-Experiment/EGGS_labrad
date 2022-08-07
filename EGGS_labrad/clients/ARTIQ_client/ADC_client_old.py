from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QComboBox, QLabel, QPushButton, QGridLayout, QFrame, QSizePolicy

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.config.device_db import device_db


class ADC_channel(QFrame):
    """
    GUI for a single ARTIQ ADC channel.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0010)
        # self.setLineWidth(2)
        self.makeLayout(name)
        self.setFixedSize(150, 150)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        title.setAlignment(Qt.AlignCenter)
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        # display
        self.display_label = QLabel('Output (V)')
        self.display = QLabel('00.00')
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setFont(QFont('MS Shell Dlg 2', pointSize=18))
        self.display.setStyleSheet('color: blue')
        # gain
        self.gain_title = QLabel('Gain')
        self.gain = QComboBox()
        self.gain.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.gain.addItems(['1', '10', '100', '1000'])
        # set layout
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(self.display_label, 1, 0)
        layout.addWidget(self.display, 2, 0, 1, 2)
        layout.addWidget(self.gain_title, 3, 0)
        layout.addWidget(self.gain, 4, 0, 1, 2)


class ADC_client(QWidget):
    """
    Client for all ADC channels.
    """

    name = "ARTIQ ADC Client"
    row_length = 8

    def __init__(self, reactor, cxn=None, parent=None):
        super(ADC_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
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
        # get artiq server and dac list
        try:
            self.artiq = yield self.cxn.artiq_server
        except Exception as e:
            print(e)
            raise

        # create holding lists
        self.sampler = None
        self.sampler_channels = {}
        for name, params in device_db.items():
            # only get devices with named class
            if 'class' not in params:
                continue
            if params['class'] == 'Sampler':
                self.sampler = name
                break
        return self.cxn

    def initializeGUI(self, cxn):
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 4)
        # layout widgets
        layout.addWidget(self._makeSamplerGroup(self.sampler))

    def _makeSamplerGroup(self, name):
        """
        Creates a group of sampler channels as a widget.
        """
        # create widget
        sampler_group = QFrame()
        sampler_group.setFrameStyle(0x0001 | 0x0010)
        sampler_group.setLineWidth(2)
        layout = QGridLayout(sampler_group)
        # set global
        sampler_header = QWidget(self)
        sampler_header_layout = QGridLayout(sampler_header)
        sampler_title = QLabel(sampler_header)
        sampler_title.setText(name)
        sampler_title.setAlignment(Qt.AlignCenter)
        sampler_title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        sampler_sample = QPushButton('Sample', sampler_header)
        sampler_sample.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        sampler_sample.clicked.connect(lambda: self.getSamples())
        sampler_reset = QPushButton('Reset', sampler_header)
        sampler_reset.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        sampler_reset.clicked.connect(lambda: self.reset())
        sampler_header_layout.addWidget(sampler_title)
        sampler_header_layout.addWidget(sampler_sample)
        sampler_header_layout.addWidget(sampler_reset)
        layout.addWidget(sampler_header, 0, 3, 1, 2)
        # layout individual channels (8 per sampler)
        for i in range(8):
            # initialize GUIs for each channel
            channel_name = name + '_' + str(i)
            channel_gui = ADC_channel(channel_name)
            # layout channel GUI
            row = int(i / self.row_length) + 2
            column = i % self.row_length
            # connect signals to slots
            channel_gui.gain.currentTextChanged.connect(lambda gain, chan=i: self.artiq.sampler_gain(chan, int(gain)))
            # add widget to client list and layout
            self.sampler_channels[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
        return sampler_group

    def startupData(self, cxn):
        for channel in self.sampler_channels.values():
            channel.lock(False)
            # channel.locks


    # SLOTS
    @inlineCallbacks
    def getSamples(self):
        resp = yield self.artiq.sampler_read(8)
        channels = self.sampler_channels.values()
        for i in range(8):
            channels[i].display.setText(str(resp[i]))

    @inlineCallbacks
    def reset(self):
        yield self.artiq.sampler_initialize()

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    # run channel GUI
    #from EGGS_labrad.clients import runGUI
    #runGUI(ADC_channel, name='ADC Channel')

    # run ADC GUI
    from EGGS_labrad.clients import runClient
    runClient(ADC_client)
