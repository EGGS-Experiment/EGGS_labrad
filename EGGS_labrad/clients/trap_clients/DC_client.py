from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch


class AMO8_channel(QFrame):
    """
    GUI for a single AMO8 DAC channel.
    """

    def __init__(self, name=None, num=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.number = num
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(275, 225)
        self.makeLayout(name)

    def makeLayout(self, title):
        layout = QGridLayout()
        # title
        self.title = QLabel(title)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        # dac
        self.dac_label = QLabel('Output Voltage (V)')
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(2)
        self.dac.setSingleStep(0.01)
        self.dac.setRange(0, 850)
        self.dac.setKeyboardTracking(False)
        # ramp
        self.ramp_start = QPushButton('Ramp')
        self.ramp_start.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        self.ramp_target_label = QLabel('End Voltage (V)')
        self.ramp_target = QDoubleSpinBox()
        self.ramp_target.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.ramp_target.setDecimals(2)
        self.ramp_target.setSingleStep(0.01)
        self.ramp_target.setRange(0, 850)
        self.ramp_target.setKeyboardTracking(False)
        self.ramp_rate_label = QLabel('Ramp Rate (V/s)')
        self.ramp_rate = QDoubleSpinBox()
        self.ramp_rate.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.ramp_rate.setDecimals(2)
        self.ramp_rate.setSingleStep(0.01)
        self.ramp_rate.setRange(0, 10)
        self.ramp_rate.setKeyboardTracking(False)
        # buttons
        self.toggleswitch = TextChangingButton(("On", "Off"))
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = Lockswitch()
        self.lockswitch.setChecked(True)

        # add widgets to layout
        layout.addWidget(self.title, 0, 0, 1, 3)
        layout.addWidget(self.dac_label, 1, 0, 1, 2)
        layout.addWidget(self.dac, 2, 0, 1, 3)
        layout.addWidget(self.ramp_target_label, 3, 1)
        layout.addWidget(self.ramp_rate_label, 3, 2)
        layout.addWidget(self.ramp_start, 4, 0, 1, 1)
        layout.addWidget(self.ramp_target, 4, 1, 1, 1)
        layout.addWidget(self.ramp_rate, 4, 2, 1, 1)
        layout.addWidget(self.toggleswitch, 5, 0)
        layout.addWidget(self.lockswitch, 5, 1)
        layout.addWidget(self.resetswitch, 5, 2)
        self.setLayout(layout)
        # connect signal to slot
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

    @inlineCallbacks
    def lock(self, status):
        yield self.resetswitch.setEnabled(status)
        yield self.dac.setEnabled(status)



class DC_client(QWidget):
    """
    Client for DC voltage control via AMO8.
    """

    name = "DC Client"
    HVID = 374861

    def __init__(self, reactor, cxn=None, parent=None):
        super(DC_client, self).__init__()
        self.reactor = reactor
        self.cxn = cxn
        self.gui = self
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
            self.amo8 = yield self.cxn.dc_server
        except Exception as e:
            print(e)
            raise
        # connect to signals
        yield self.amo8.signal__hv_update(self.HVID)
        yield self.amo8.addListener(listener=self.updateHV, source=None, ID=self.HVID)
        # todo: make client class
        self.amo8_channels = []
        # config
        try:
            from EGGS_labrad.config.dc_config import dcConfig
            self.active_channels = dcConfig.channeldict
            self.row_length = dcConfig.rowLength
        except Exception as e:
            print(e)
        return self.cxn

    def createGUI(self, cxn):
        # set client title
        self.setWindowTitle('Trap DC Client')
        amo8_layout = QGridLayout()
        # create header
        self.device_header = self._createHeader()
        # layout individual channels (chosen via class variable)
        channel_names = list(self.active_channels.keys())
        channel_numbers = list(self.active_channels.values())
        for group in self.active_channels.values():
            for channel_name, channel_params in group.items():
                # initialize GUIs for each channel
                channel_gui = AMO8_channel(channel_name, channel_params['num'])
                # add widget to client list and layout
                self.amo8_channels.append(channel_gui)
                amo8_layout.addWidget(channel_gui, channel_params['row'], channel_params['col'])
        # layout rest of device
        amo8_layout.addWidget(self.device_header, 0, int(self.row_length / 2), 1, 1)
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
        self.device_hv_monitor = QFrame(device_header)
        self.device_hv_monitor.setFrameStyle(0x0001 | 0x0030)
        device_hv_monitor_layout = QGridLayout(self.device_hv_monitor)
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
        self.device_global_onswitch = QPushButton('ALL ON')
        self.device_global_onswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.device_global_offswitch = QPushButton('ALL OFF')
        self.device_global_offswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.device_global_clear = QPushButton('ALL CLEAR')
        self.device_global_clear.setFont(QFont('MS Shell Dlg 2', pointSize=10))
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
        device_header_layout.addWidget(device_header_title, 0, 0, 1, 2)
        device_header_layout.addWidget(self.device_global_onswitch, 1, 0, 1, 1)
        device_header_layout.addWidget(self.device_global_offswitch, 2, 0, 1, 1)
        device_header_layout.addWidget(self.device_global_clear, 3, 0, 1, 1)
        device_header_layout.addWidget(self.device_hv_monitor, 1, 1, 3, 1)
        return device_header

    @inlineCallbacks
    def initData(self, cxn):
        try:
            voltage_list = yield self.amo8.voltage(-1)
            voltage_list = [voltage_list[channel.number] for channel in self.amo8_channels]
            toggle_list = yield self.amo8.toggle(-1)
            toggle_list = [toggle_list[channel.number] for channel in self.amo8_channels]
            for i in range(len(self.amo8_channels)):
                self.amo8_channels[i].dac.setValue(voltage_list[i])
                self.amo8_channels[i].toggle.setChecked(toggle_list[i])
        except Exception as e:
            print(e)

    def initializeGUI(self, cxn):
        # connect global signals
        self.device_global_onswitch.clicked.connect(lambda: self.amo8.toggle(-1, 1))
        self.device_global_offswitch.clicked.connect(lambda: self.amo8.toggle(-1, 0))
        self.device_global_clear.clicked.connect(lambda: self.amo8.clear())
        # connect each channel
        for channel in self.amo8_channels:
            channel.dac.valueChanged.connect(lambda value: self.amo8.voltage(channel.number, value))
            channel.ramp_start.clicked.connect(lambda voltage=channel.ramp_target.value(), rate=channel.ramp_rate.value():
                                               self.self.amo8.ramp(channel.number, voltage, rate))
            channel.toggle.clicked.connect(lambda status=channel.lockswitch.isChecked():
                                           self.amo8.toggle(channel.number, status))
            channel.resetswitch.clicked.connect(lambda: self.reset(channel.number))


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        yield self.amo8.voltage(channel_num, 0)
        yield self.amo8.toggle(channel_num, 0)

    def updateHV(self, hv):
        self.gui.device_hv_monitor.device_hv_v1.setText(str(hv[0]))
        self.gui.device_hv_monitor.device_hv_v2.setText(str(hv[1]))
        self.gui.device_hv_monitor.device_hv_i1.setText(str(hv[2]))
        self.gui.device_hv_monitor.device_hv_i2.setText(str(hv[3]))

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI, runClient
    # run channel GUI
    #runGUI(AMO8_channel, name='AMO8 Channel')
    # run DAC GUI
    runClient(DC_client)
