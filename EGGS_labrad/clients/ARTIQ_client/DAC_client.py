from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.Widgets import TextChangingButton


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
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        dac_label = QLabel('DAC Register')
        off_label = QLabel('Offset Register')
        gain_label = QLabel('Gain Register')

        # editable fields
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(0)
        self.dac.setSingleStep(1)
        self.dac.setRange(0, 0xffff)
        self.dac.setKeyboardTracking(False)
        self.dac.setAlignment(Qt.AlignRight)
        self.gain = QDoubleSpinBox()
        self.gain.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.gain.setDecimals(0)
        self.gain.setSingleStep(1)
        self.gain.setRange(0, 0xffff)
        self.gain.setKeyboardTracking(False)
        self.gain.setAlignment(Qt.AlignRight)
        self.off = QDoubleSpinBox()
        self.off.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.off.setDecimals(0)
        self.off.setSingleStep(1)
        self.off.setRange(0, 0xffff)
        self.off.setKeyboardTracking(False)
        self.off.setAlignment(Qt.AlignRight)

        # buttons
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.calibrateswitch = QPushButton('Calibrate')
        self.calibrateswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status: self.lock(status))

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

    def lock(self, status):
        self.resetswitch.setEnabled(status)
        self.calibrateswitch.setEnabled(status)
        self.dac.setEnabled(status)
        self.off.setEnabled(status)
        self.gain.setEnabled(status)


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
        # start connections
        d = self.connect()
        d.addCallback(self.getDevices)
        d.addCallback(self.initializeGUI)
        d.addCallback(self.startupData)

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
        self.zotino_list = []
        self.ad5372_clients = {}
        for name, params in device_db.items():
            # only get devices with named class
            if 'class' not in params:
                continue
            if params['class'] in ('Zotino', 'Fastino'):
                self.zotino_list.append(name)
        return self.cxn

    def initializeGUI(self, cxn):
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 4)
        # layout widgets
        for i in range(len(self.zotino_list)):
            name = self.zotino_list[i]
            zotino_group = self._makeZotinoGroup(name)
            layout.addWidget(zotino_group, 2 + i, 0)

    def _makeZotinoGroup(self, name):
        """
        Creates a group of zotino channels as a widget.
        """
        # create widget
        zotino_group = QFrame()
        zotino_group.setFrameStyle(0x0001 | 0x0010)
        zotino_group.setLineWidth(2)
        layout = QGridLayout(zotino_group)
        # set global
        zotino_header = QWidget(self)
        zotino_header_layout = QGridLayout(zotino_header)
        zotino_title = QLabel(name, zotino_header)
        zotino_title.setAlignment(Qt.AlignCenter)
        zotino_title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        zotino_global_ofs_title = QLabel('Global Offset Register', zotino_header)
        zotino_global_ofs = QDoubleSpinBox(zotino_header)
        zotino_global_ofs.setMaximum(0x2fff)
        zotino_global_ofs.setMinimum(0)
        zotino_global_ofs.setDecimals(0)
        zotino_global_ofs.setSingleStep(1)
        zotino_global_ofs.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        zotino_global_ofs.setAlignment(Qt.AlignCenter)
        zotino_global_ofs.valueChanged.connect(lambda voltage_mu: self.artiq.dac_ofs(voltage_mu, 'mu'))
        zotino_header_layout.addWidget(zotino_title)
        zotino_header_layout.addWidget(zotino_global_ofs_title)
        zotino_header_layout.addWidget(zotino_global_ofs)
        layout.addWidget(zotino_header, 0, 2, 1, 2)
        # layout individual channels (32 per zotino)
        for i in range(32):
            # initialize GUIs for each channel
            channel_name = name + '_' + str(i)
            channel_gui = AD5372_channel(channel_name)
            # layout channel GUI
            row = int(i / self.row_length) + 2
            column = i % self.row_length
            # connect signals to slots
            channel_gui.dac.valueChanged.connect(lambda voltage_mu, channel_num=i: self.artiq.dac_set(channel_num, voltage_mu, 'mu'))
            channel_gui.off.valueChanged.connect(lambda voltage_mu, channel_num=i: self.artiq.dac_offset(channel_num, voltage_mu, 'mu'))
            channel_gui.gain.valueChanged.connect(lambda gain_mu, channel_num=i: self.artiq.dac_offset(channel_num, gain_mu, 'mu'))
            channel_gui.calibrateswitch.clicked.connect(lambda: self.calibrate)
            channel_gui.resetswitch.clicked.connect(lambda: self.reset)
            # add widget to client list and layout
            self.ad5372_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
            # print(name + ' - row:' + str(row) + ', column: ' + str(column))
        return zotino_group

    def startupData(self, cxn):
        for channel in self.ad5372_clients.values():
            channel.lock(False)
            # todo: finish


    # SLOTS
    @inlineCallbacks
    def calibrate(self):
        pass

    @inlineCallbacks
    def reset(self, channel_num):
        yield self.artiq.dac_set(channel_num, 0, 'mu')
        yield self.artiq.dac_offset(channel_num, 0, 'mu')
        yield self.artiq.dac_set(channel_num, 0, 'mu')

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    # run channel GUI
    # from EGGS_labrad.clients import runGUI
    # runGUI(AD5372_channel, name='AD5372 Channel')

    # run DAC GUI
    from EGGS_labrad.clients import runClient
    runClient(DAC_client)
