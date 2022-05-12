from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox, QClientMenuHeader


class AMO8_channel(QFrame):
    """
    GUI for a single AMO8 DAC channel.
    """

    def __init__(self, name=None, num=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.number = num
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(270, 200)
        self.makeLayout(name)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # title
        self.title = QLabel(title)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        self.title.setAlignment(Qt.AlignCenter)
        # dac
        self.dac_label = QLabel('Output Voltage (V)')
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=14))
        self.dac.setDecimals(2)
        self.dac.setSingleStep(0.01)
        self.dac.setRange(0, 850)
        self.dac.setKeyboardTracking(False)
        # ramp
        self.ramp_start = QPushButton('Ramp')
        self.ramp_start.setFont(QFont('MS Shell Dlg 2', pointSize=11))
        self.ramp_target_label = QLabel('End Voltage (V)')
        self.ramp_target = QDoubleSpinBox()
        self.ramp_target.setFont(QFont('MS Shell Dlg 2', pointSize=14))
        self.ramp_target.setDecimals(1)
        self.ramp_target.setSingleStep(0.1)
        self.ramp_target.setRange(0, 850)
        self.ramp_target.setKeyboardTracking(False)
        self.ramp_rate_label = QLabel('Ramp Rate (V/s)')
        self.ramp_rate = QDoubleSpinBox()
        self.ramp_rate.setFont(QFont('MS Shell Dlg 2', pointSize=14))
        self.ramp_rate.setDecimals(1)
        self.ramp_rate.setSingleStep(0.1)
        self.ramp_rate.setRange(0, 1000)
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
        # connect signal to slot
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

    @inlineCallbacks
    def lock(self, status):
        yield self.resetswitch.setEnabled(status)
        yield self.dac.setEnabled(status)


class DC_gui(QFrame):
    """
    GUI for the AMO8 high voltage box.
    """

    def __init__(self, name=None):
        super().__init__()
        self.amo8_channels = {}
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        #self.setFixedSize(575, 675)
        # config
        try:
            from EGGS_labrad.config.dc_config import dc_config
            self.headerLayout = dc_config.headerLayout
            self.active_channels = dc_config.channeldict
        except Exception as e:
            print(e)
        # create GUI
        self.createGUI()

    def createGUI(self):
        self.setFrameStyle(0x0001 | 0x0030)
        # set client title
        self.setWindowTitle('DC Client')
        amo8_layout = QGridLayout(self)
        # create header
        self.header = QClientMenuHeader()
        self.global_buttons = self._createGlobalButtons()
        self.hv_monitor = self._createHVmonitor()
        self.device_title = QLabel(self.name)
        self.device_title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        self.device_title.setAlignment(Qt.AlignCenter)
        # create holder widget for the channels
        channel_holder = QWidget()
        channel_holder_layout = QGridLayout(channel_holder)
        # add channel buttons to channel_holder
        self.doubleramp_endcaps = QPushButton("Ramp Both Endcaps")
        self.doubleramp_aramp = QPushButton("Ramp Both Trap Rods")
        self.triangleramp_aramp = QPushButton("Triangle Ramp Both Trap Rods")
        channel_holder_layout.addWidget(self.doubleramp_endcaps,        0, 0)
        channel_holder_layout.addWidget(self.doubleramp_aramp,          0, 2)
        channel_holder_layout.addWidget(self.triangleramp_aramp,        1, 2)
        shift_rows = 2# tmp remove todo
        for channel_name, channel_params in self.active_channels.items():
            channel_num = channel_params['num']
            # initialize GUIs for each channel
            channel_gui = AMO8_channel(channel_name, channel_num)
            # add widget to client list and layout
            self.amo8_channels[channel_num] = channel_gui
            channel_holder_layout.addWidget(channel_gui, channel_params['row'] + shift_rows, channel_params['col'])
        channel_holder_wrapped = QCustomGroupBox(channel_holder, "DC Channels", scrollable=True)
        # lay out device
        amo8_layout.setMenuBar(self.header)
        amo8_layout.addWidget(self.device_title,            0, 0, 1, 1)
        amo8_layout.addWidget(self.global_buttons,          0, 1, 1, 1)
        amo8_layout.addWidget(self.hv_monitor,              0, 2, 1, 1)
        amo8_layout.addWidget(channel_holder_wrapped,       1, 0, 5, 3)

    def _createGlobalButtons(self):
        # create header layout
        global_widget = QWidget()
        global_widget_layout = QGridLayout(global_widget)
        # create global buttons
        self.device_global_onswitch = QPushButton('ALL ON')
        self.device_global_onswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.device_global_offswitch = QPushButton('ALL OFF')
        self.device_global_offswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.device_global_clear = QPushButton('ALL CLEAR')
        self.device_global_clear.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        # lay out header
        global_widget_layout.addWidget(self.device_global_onswitch,         0, 0, 1, 1)
        global_widget_layout.addWidget(self.device_global_offswitch,        0, 1, 1, 1)
        global_widget_layout.addWidget(self.device_global_clear,            0, 2, 1, 1)
        # wrap device header
        wrapped_device_header = QCustomGroupBox(global_widget, "Global Settings")
        return wrapped_device_header

    def _createHVmonitor(self):
        # create header layout
        hv_widget = QWidget()
        hv_widget_layout = QGridLayout(hv_widget)
        # create HV monitor displays
        device_hv_v1_label = QLabel('HV Input V1 (V)')
        self.device_hv_v1 = QLabel('V1')
        self.device_hv_v1.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.device_hv_v1.setStyleSheet('color: red')
        self.device_hv_v1.setAlignment(Qt.AlignRight)
        device_hv_i1_label = QLabel('HV Input I1 (mA)')
        self.device_hv_i1 = QLabel('I1')
        self.device_hv_i1.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.device_hv_i1.setStyleSheet('color: red')
        self.device_hv_i1.setAlignment(Qt.AlignRight)
        # lay out header
        hv_widget_layout.addWidget(device_hv_v1_label,                  0, 0, 1, 1)
        hv_widget_layout.addWidget(self.device_hv_v1,                   1, 0, 1, 1)
        hv_widget_layout.addWidget(device_hv_i1_label,                  0, 1, 1, 1)
        hv_widget_layout.addWidget(self.device_hv_i1,                   1, 1, 1, 1)
        # wrap device header
        wrapped_device_header = QCustomGroupBox(hv_widget, "HV Monitor")
        return wrapped_device_header


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # runGUI(AMO8_channel, name='AMO8 Channel')
    runGUI(DC_gui, name='DC Client')
