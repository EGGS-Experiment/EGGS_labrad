from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.Widgets import TextChangingButton, Lockswitch


class AMO8_channel(QFrame):
    """
    GUI for a single AMO8 DAC channel.
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
        title.setAlignment(Qt.AlignCenter)
        dac_label = QLabel('Output Voltage (V)')

        # editable fields
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(2)
        self.dac.setSingleStep(0.01)
        self.dac.setRange(0, 850)
        self.dac.setKeyboardTracking(False)

        # buttons
        self.toggleswitch = TextChangingButton(("On", "Off"))
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = Lockswitch()
        self.lockswitch.setChecked(True)

        # add widgets to layout
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(dac_label, 1, 0, 1, 1)
        layout.addWidget(self.dac, 2, 0, 1, 3)
        layout.addWidget(self.toggleswitch, 3, 0)
        layout.addWidget(self.lockswitch, 3, 1)
        layout.addWidget(self.resetswitch, 3, 2)
        self.setLayout(layout)
        # connect signal to slot
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

    @inlineCallbacks
    def lock(self, status):
        yield self.resetswitch.setEnabled(status)
        yield self.dac.setEnabled(status)

#todo: try client class

class endcap_client(QWidget):
    """
    Client for endcap control via AMO8.
    """
#TODO: signal for hv in
    #todo: get endcap config
    #todo: ramping
    name = "Endcap Client"
    row_length = 6
    active_channels = range(0, 32)

    def __init__(self, reactor, cxn=None, parent=None):
        super(endcap_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
        # initialization sequence
        d = self.connectLabrad()
        d.addCallback(self.createGUI)
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)


    # STARTUP
    @inlineCallbacks
    def connectLabrad(self):
        # connect to LabRAD
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        # get servers
        try:
            self.amo8 = yield self.cxn.amo8_server
        except Exception as e:
            print(e)
            raise
        # todo: connect signals
        # create dictionary to hold channels
        self.amo8_channels = {}
        self.device_elements = {} #todo: access widgets
        return self.cxn

    def createGUI(self, cxn):
        # set client title
        self.setWindowTitle('AMO8 Endcap Client')
        amo8_layout = QGridLayout()
        # create header
        device_header = self._createHeader()
        # layout individual channels (chosen via class variable)
        for i in self.active_channels:
            # initialize GUIs for each channel
            channel_name = 'CH' + str(i + 1)
            channel_gui = AMO8_channel(channel_name)
            # layout channel GUI
            row = int(i / self.row_length) + 2
            column = i % self.row_length
            # add widget to client list and layout
            self.amo8_channels[channel_name] = channel_gui
            amo8_layout.addWidget(channel_gui, row, column)
        # layout rest of device
        amo8_layout.addWidget(device_header, 0, 2, 2, 2)
        self.setLayout(amo8_layout)

    def _createHeader(self):
        # create header layout
        device_header = QWidget(self)
        device_header_layout = QGridLayout(device_header)
        # create header title
        device_header_title = QLabel(self.name, device_header)
        device_header_title.setAlignment(Qt.AlignCenter)
        device_header_title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        # create HV monitor widget
        device_hv_monitor = QFrame(device_header)
        device_hv_monitor.setFrameStyle(0x0001 | 0x0030)
        device_hv_monitor_layout = QGridLayout(device_hv_monitor)
        # create HV monitor displays
        device_hv_v1_label = QLabel('V1 (V)')
        device_hv_v1 = QLabel('V1')
        device_hv_v1.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        device_hv_v1.setStyleSheet('color: red')
        device_hv_v2_label = QLabel('V2 (V)')
        device_hv_v2 = QLabel('V2')
        device_hv_v2.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        device_hv_v2.setStyleSheet('color: red')
        device_hv_i1_label = QLabel('I1 (mA)')
        device_hv_i1 = QLabel('I1')
        device_hv_i1.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        device_hv_i1.setStyleSheet('color: red')
        device_hv_i2_label = QLabel('I2 (mA)')
        device_hv_i2 = QLabel('I2')
        device_hv_i2.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        device_hv_i2.setStyleSheet('color: red')
        # create global buttons
        device_global_onswitch = QPushButton('ALL ON')
        device_global_onswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        device_global_offswitch = QPushButton('ALL OFF')
        device_global_offswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        device_global_clear = QPushButton('ALL CLEAR')
        device_global_clear.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        # lay out HV monitor
        device_hv_title = QLabel('HV Input')
        device_hv_title.setFont(QFont('MS Shell Dlg 2', pointSize=14))
        device_hv_title.setAlignment(Qt.AlignCenter)
        device_hv_monitor_layout.addWidget(device_hv_title, 0, 0, 1, 2)
        device_hv_monitor_layout.addWidget(device_hv_v1_label, 1, 0)
        device_hv_monitor_layout.addWidget(device_hv_v2_label, 1, 1)
        device_hv_monitor_layout.addWidget(device_hv_v1, 2, 0)
        device_hv_monitor_layout.addWidget(device_hv_v2, 2, 1)
        device_hv_monitor_layout.addWidget(device_hv_i1_label, 3, 0)
        device_hv_monitor_layout.addWidget(device_hv_i2_label, 3, 1)
        device_hv_monitor_layout.addWidget(device_hv_i1, 4, 0)
        device_hv_monitor_layout.addWidget(device_hv_i2, 4, 1)
        # lay out header
        device_header_layout.addWidget(device_header_title, 0, 0, 1, 3)
        device_header_layout.addWidget(device_global_onswitch, 1, 0)
        device_header_layout.addWidget(device_global_offswitch, 2, 0)
        device_header_layout.addWidget(device_global_clear, 3, 0)
        device_header_layout.addWidget(device_hv_monitor, 1, 1, 3, 2)
        return device_header

    @inlineCallbacks
    def initData(self, cxn):
        voltage_list = yield self.amo8.voltage(-1)
        toggle_list = yield self.amo8.toggle(-1)
        for i in range(len(self.amo8_channels)):
            self.amo8_channels[i].dac.setValue(voltage_list[i])
            self.amo8_channels[i].toggle.setChecked(toggle_list[i])

    def initializeGUI(self, cxn):
        # connect global signals
        self.device_global_onswitch.clicked.connect(lambda: self.amo8.toggle(-1, 1))
        self.device_global_offswitch.clicked.connect(lambda: self.amo8.toggle(-1, 0))
        self.device_global_clear.clicked.connect(lambda: self.amo8.clear())
        # connect each channel
        for chan_num in range(len(self.amo8_channels)):
            channel = self.amo8_channels[chan_num]
            channel.dac.valueChanged.connect(lambda value: self.amo8.voltage(chan_num, value))
            channel.ramp.clicked.connect(lambda: self.prepareRamp(chan_num))
            channel.toggle.clicked.connect(lambda status=self.lockswitch.isChecked(): self.amo8.toggle(chan_num, status))
            channel.resetswitch.clicked.connect(lambda: self.reset(chan_num))


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        yield self.amo8.voltage(channel_num, 0)
        yield self.amo8.toggle(channel_num, 0)

    @inlineCallbacks
    def prepareRamp(self, channel_num):
        #todo: pop up for v_final and rate
        #todo: update after clicked
        yield self.amo8.ramp(channel_num, v_final, rate)

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    # run channel GUI
    from EGGS_labrad.lib.clients import runGUI, runClient
    #runGUI(AMO8_channel, name='AMO8 Channel')

    # run DAC GUI
    runClient(endcap_client)
