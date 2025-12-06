from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QFrame, QSizePolicy, QWidget, QLabel,\
    QGridLayout, QDoubleSpinBox, QComboBox, QHBoxLayout, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox

_SHELL_FONT = 'MS Shell Dlg 2'


class SLS_gui(QFrame):

    def __init__(self, channelinfo=None):
        super().__init__()
        self.setWindowTitle('SLS Client')
        self.setFrameStyle(0x0001 | 0x0030)
        # self.setFixedSize(680, 410)
        self.makeLayout()
        for widget in (self.autolock_lockswitch, self.offset_lockswitch, self.PDH_lockswitch, self.servo_lockswitch):
            widget.setChecked(False)

    def _makeAutolockWidget(self):
        autolock_widget = QWidget(self)
        autolock_layout = QVBoxLayout(autolock_widget)

        autolock_param_label = QLabel("Sweep Parameter")
        # autolock_time_label = QLabel("Lock Time (d:h:m)")
        autolock_toggle_label = QLabel("Autolock")
        autolock_attempts_label = QLabel("Lock Attempts")
        autolock_status_label = QLabel("Autolock Status")
        #
        # self.autolock_time = QLabel("Time")
        # self.autolock_time.setAlignment(Qt.AlignCenter)
        # self.autolock_time.setFont(QFont(_SHELL_FONT, pointSize=18))
        # self.autolock_time.setStyleSheet('color: blue')
        self.autolock_param = QComboBox()

        for item_text in ("Off", "PZT", "Current"):
            self.autolock_param.addItem(item_text)

        self.autolock_attempts = QLabel("NULL", )
        self.autolock_attempts.setAlignment(Qt.AlignCenter)
        self.autolock_attempts.setFont(QFont(_SHELL_FONT, pointSize=18))
        self.autolock_attempts.setStyleSheet('color: blue')

        self.autolock_status = QLabel("FALSE")
        self.autolock_status.setAlignment(Qt.AlignCenter)
        self.autolock_status.setFont(QFont(_SHELL_FONT, pointSize=16))
        self.autolock_status.setStyleSheet('color: blue')
        self.autolock_toggle = TextChangingButton(('On', 'Off'))

        for widget in (autolock_attempts_label, self.autolock_attempts,
                        autolock_status_label, self.autolock_status,
                       autolock_toggle_label, self.autolock_toggle, autolock_param_label, self.autolock_param):
            autolock_layout.addWidget(widget)
        return QCustomGroupBox(autolock_widget, "Autolock")

    def _makeOffsetWidget(self):
        offset_widget = QWidget()
        offset_layout = QVBoxLayout(offset_widget)

        offset_lockpoint_label = QLabel("Lockpoint")
        offset_eom_rf_amp_label = QLabel("EOM RF Amplitude")
        offset_freq_label = QLabel("Offset Frequency (MHz)")

        self.offset_freq = QDoubleSpinBox()
        self.offset_freq.setRange(10.0, 800.0)
        self.offset_freq.setSingleStep(1.0)

        self.offset_eom_rf_amp = QDoubleSpinBox()
        self.offset_eom_rf_amp.setRange(0.0, 100.0)
        self.offset_eom_rf_amp.setSingleStep(0.1)

        self.offset_lockpoint = QComboBox()
        for item_text in ("J(+2)", "J(+1)", "Resonance", "J(-1)", "J(-2)"):
            self.offset_lockpoint.addItem(item_text)

        for widget in (offset_freq_label, self.offset_freq, offset_eom_rf_amp_label, self.offset_eom_rf_amp,
                       offset_lockpoint_label, self.offset_lockpoint):
            offset_layout.addWidget(widget)
        return QCustomGroupBox(offset_widget, "Offset Lock")

    def _makePDHWidget(self):
        PDH_widget = QWidget()
        PDH_layout = QVBoxLayout(PDH_widget)

        PDH_filter_label = QLabel("Filter Index")
        PDH_phasemodulation_label = QLabel("Phase modulation (rad)")
        PDH_phaseoffset_label = QLabel("Reference phase (deg)")
        PDH_freq_label = QLabel("Frequency (MHz)")

        self.PDH_freq = QDoubleSpinBox(PDH_widget)
        self.PDH_freq.setRange(10.0, 35.0)
        self.PDH_freq.setSingleStep(0.1)
        self.PDH_filter = QComboBox(PDH_widget)
        self.PDH_filter.addItem("None")
        for i in range(1, 16):
            self.PDH_filter.addItem(str(i))

        self.PDH_phaseoffset = QDoubleSpinBox()
        self.PDH_phaseoffset.setMaximum(360.0)
        self.PDH_phaseoffset.setSingleStep(0.1)
        self.PDH_phasemodulation = QDoubleSpinBox()
        self.PDH_phasemodulation.setMaximum(3.0)
        self.PDH_phasemodulation.setSingleStep(0.1)

        for widget in (PDH_freq_label, self.PDH_freq, PDH_phasemodulation_label, self.PDH_phasemodulation,
                       PDH_phaseoffset_label, self.PDH_phaseoffset, PDH_filter_label, self.PDH_filter):
            PDH_layout.addWidget(widget)
        return QCustomGroupBox(PDH_widget, "PDH")

    def _makeServoWidget(self):
        servo_widget = QWidget(self)
        servo_layout = QVBoxLayout(servo_widget)

        servo_param_label = QLabel("Parameter")
        servo_set_label = QLabel("Setpoint")
        servo_p_label = QLabel("Proportional")
        servo_i_label = QLabel("Integral")
        servo_d_label = QLabel("Differential")
        servo_filter_label = QLabel("Filter Index")

        self.servo_filter = QComboBox()
        self.servo_filter.addItem("None")
        for i in range(1, 16):
            self.servo_filter.addItem(str(i))

        self.servo_set = QDoubleSpinBox()
        self.servo_set.setRange(-1000000.0, 1000000.0)
        self.servo_p = QDoubleSpinBox()
        self.servo_p.setMaximum(1000.0)
        self.servo_i = QDoubleSpinBox()
        self.servo_i.setMaximum(1.0)
        self.servo_i.setSingleStep(0.01)
        self.servo_d = QDoubleSpinBox()
        self.servo_d.setMaximum(10000.0)
        self.servo_param = QComboBox()
        for item_text in ("Current", "PZT", "TX"):
            self.servo_param.addItem(item_text)

        for widget in (servo_param_label, self.servo_param, servo_set_label, self.servo_set, servo_p_label, self.servo_p,
                       servo_i_label, self.servo_i, servo_d_label, self.servo_d, servo_filter_label, self.servo_filter):
            servo_layout.addWidget(widget)
        return QCustomGroupBox(servo_widget, "PID")

    def makeLayout(self):
        # make widgets
        self.PDH_widget = self._makePDHWidget()
        self.offset_widget = self._makeOffsetWidget()
        self.servo_widget = self._makeServoWidget()
        self.autolock_widget = self._makeAutolockWidget()

        # for widget in (self.autolock_widget, self.offset_widget, self.PDH_widget, self.servo_widget):
        #     # widget.setFixedWidth(161)

        # lockswitches
        self.PDH_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.PDH_lockswitch.toggled.connect(lambda status, widget=self.PDH_widget: self._lock(status, widget))
        self.servo_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.servo_lockswitch.toggled.connect(lambda status, widget=self.servo_widget: self._lock(status, widget))
        self.autolock_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.autolock_lockswitch.toggled.connect(lambda status, widget=self.autolock_widget: self._lock(status, widget))
        self.offset_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.offset_lockswitch.toggled.connect(lambda status, widget=self.offset_widget: self._lock(status, widget))

        # title
        sls_label = QLabel("SLS Client", self)
        sls_label.setFont(QFont(_SHELL_FONT, pointSize=20))
        sls_label.setAlignment(Qt.AlignCenter)

        # lay out
        layout = QGridLayout(self)
        layout.addWidget(sls_label,                             0, 0, 1, 7)
        layout.addWidget(self.autolock_lockswitch,              1, 0, 1, 4)
        layout.addWidget(self.autolock_widget,          2, 0, 7, 4)
        layout.addWidget(self.offset_lockswitch,          1, 4, 1, 1)
        layout.addWidget(self.offset_widget,               2, 4, 4, 1)
        layout.addWidget(self.PDH_lockswitch,                   1, 5, 1, 1)
        layout.addWidget(self.PDH_widget,               2, 5, 6, 1)
        layout.addWidget(self.servo_lockswitch,                 1, 6, 1, 1)
        layout.addWidget(self.servo_widget,             2, 6, 10, 1)

    def _lock(self, status, widget):
        widget.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SLS_gui)
