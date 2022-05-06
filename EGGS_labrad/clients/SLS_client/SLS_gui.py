from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QFrame, QSizePolicy, QWidget, QLabel, QGridLayout, QDoubleSpinBox, QComboBox, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox


class SLS_gui(QFrame):

    def __init__(self, channelinfo=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle('SLS Client')
        self.setFixedSize(587, 410)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.makeWidgets()
        self.makeLayout()

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        # TITLE
        self.sls_label = QLabel("thkim", self)
        # AUTOLOCK
        self.autolock_widget = QWidget(self)
        self.autolock_layout = QVBoxLayout(self.autolock_widget)
        self.autolock_param_label = QLabel("Sweep Parameter", self.autolock_widget)
        self.autolock_time = QLabel(self.autolock_widget)
        self.autolock_time.setAlignment(Qt.AlignCenter)
        self.autolock_time.setFont(QFont(shell_font, pointSize=18))
        self.autolock_time.setStyleSheet('color: blue')
        self.autolock_param = QComboBox(self.autolock_widget)
        self.autolock_param.addItem("Off")
        self.autolock_param.addItem("PZT")
        self.autolock_param.addItem("Current")
        self.autolock_time_label = QLabel("Lock Time (d:h:m)", self.autolock_widget)
        self.autolock_toggle_label = QLabel("Autolock", self.autolock_widget)
        self.autolock_attempts = QLabel(self.autolock_widget)
        self.autolock_attempts.setAlignment(Qt.AlignCenter)
        self.autolock_attempts.setFont(QFont(shell_font, pointSize=18))
        self.autolock_attempts.setStyleSheet('color: blue')
        self.autolock_attempts_label = QLabel("Lock Attempts", self.autolock_widget)
        self.autolock_toggle = TextChangingButton(('On', 'Off'), self.autolock_widget)
        self.autolock_lockswitch = TextChangingButton(('Unlocked', 'Locked'), self.autolock_widget)
        for widget in (self.autolock_lockswitch, self.autolock_time_label, self.autolock_time,
                       self.autolock_attempts_label, self.autolock_attempts, self.autolock_toggle_label,
                       self.autolock_toggle, self.autolock_param_label, self.autolock_param):
            self.autolock_layout.addWidget(widget)
        # OFFSET LOCK
        self.off_widget = QWidget(self)
        self.off_layout = QVBoxLayout(self.off_widget)
        self.off_lockpoint_label = QLabel("Lockpoint", self.off_widget)
        self.off_freq_label = QLabel("Offset Frequency (MHz)", self.off_widget)
        self.off_freq = QDoubleSpinBox(self.off_widget)
        self.off_freq.setMinimum(10.0)
        self.off_freq.setMaximum(35.0)
        self.off_freq.setSingleStep(0.1)
        self.off_lockswitch = TextChangingButton(('Unlocked', 'Locked'), self.off_widget)
        self.off_lockpoint = QComboBox(self.off_widget)
        self.off_lockpoint.addItem("J(+2)")
        self.off_lockpoint.addItem("J(+1)")
        self.off_lockpoint.addItem("Resonance")
        self.off_lockpoint.addItem("J(-1)")
        self.off_lockpoint.addItem("J(-2)")
        for widget in (self.off_lockswitch, self.off_freq_label, self.off_freq,
                       self.off_lockpoint_label, self.off_lockpoint):
            self.off_layout.addWidget(widget)
        # PDH
        self.PDH_widget = QWidget(self)
        self.PDH_layout = QVBoxLayout(self.PDH_widget)
        self.PDH_freq = QDoubleSpinBox(self.PDH_widget)
        self.PDH_freq.setMinimum(10.0)
        self.PDH_freq.setMaximum(35.0)
        self.PDH_freq.setSingleStep(0.1)
        self.PDH_freq_label = QLabel("Frequency (MHz)", self.PDH_widget)
        self.PDH_filter = QComboBox(self.PDH_widget)
        self.PDH_filter.addItem("None")
        for i in range(1, 16):
            self.PDH_filter.addItem(str(i))
        self.PDH_filter_label = QLabel("Filter Index", self.PDH_widget)
        self.PDH_phaseoffset = QDoubleSpinBox(self.PDH_widget)
        self.PDH_phaseoffset.setMaximum(360.0)
        self.PDH_phaseoffset.setSingleStep(0.1)
        self.PDH_phasemodulation_label = QLabel("Phase modulation (rad)", self.PDH_widget)
        self.PDH_phasemodulation = QDoubleSpinBox(self.PDH_widget)
        self.PDH_phasemodulation.setMaximum(3.0)
        self.PDH_phasemodulation.setSingleStep(0.1)
        self.PDH_phaseoffset_label = QLabel("Reference phase (deg)", self.PDH_widget)
        self.PDH_lockswitch = TextChangingButton(('Unlocked', 'Locked'), self.PDH_widget)
        for widget in (self.PDH_lockswitch, self.PDH_freq_label, self.PDH_freq,
                       self.PDH_phasemodulation_label, self.PDH_phasemodulation, self.PDH_phaseoffset_label,
                       self.PDH_phaseoffset, self.PDH_filter_label, self.PDH_filter):
            self.PDH_layout.addWidget(widget)
        # PID
        self.servo_widget = QWidget(self)
        self.servo_layout = QVBoxLayout(self.servo_widget)
        self.servo_filter = QComboBox(self.servo_widget)
        self.servo_filter.addItem("None")
        for i in range(1, 16):
            self.servo_filter.addItem(str(i))
        self.servo_set = QDoubleSpinBox(self.servo_widget)
        self.servo_set.setMinimum(-1000000.0)
        self.servo_set.setMaximum(1000000.0)
        self.servo_p = QDoubleSpinBox(self.servo_widget)
        self.servo_p.setMaximum(1000.0)
        self.servo_param = QComboBox("Parameter", self.servo_widget)
        self.servo_param.addItem("Current")
        self.servo_param.addItem("PZT")
        self.servo_param.addItem("TX")
        self.servo_p_label = QLabel("Proportional", self.servo_widget)
        self.servo_i = QDoubleSpinBox(self.servo_widget)
        self.servo_i.setMaximum(1.0)
        self.servo_i.setSingleStep(0.01)
        self.servo_i_label = QLabel("Integral", self.servo_widget)
        self.servo_param_label = QLabel("Filter Index", self.servo_widget)
        self.servo_filter_label = QLabel(self.servo_widget)
        self.servo_d_label = QLabel("Differential", self.servo_widget)
        self.servo_set_label = QLabel("Setpoint", self.servo_widget)
        self.servo_d = QDoubleSpinBox(self.servo_widget)
        self.servo_d.setMaximum(10000.0)
        self.servo_lockswitch = TextChangingButton(('Unlocked', 'Locked'), self.servo_widget)
        for widget in (self.servo_lockswitch, self.servo_param_label, self.servo_param,
                       self.servo_set_label, self.servo_set, self.servo_p_label, self.servo_p,
                       self.servo_i_label, self.servo_i, self.servo_d_label, self.servo_d,
                       self.servo_filter_label, self.servo_filter):
            self.servo_layout.addWidget(widget)
        #self.autolock_time.setText(_translate("self", "<html><head/><body><p align=\"center\"><span style=\" font-size:18pt; color:#0055ff;\">Time</span></p></body></html>"))
        #self.sls_label.setText(_translate("self", "<html><head/><body><p align=\"center\"><span style=\" font-size:20pt;\">SLS Laser Client</span></p></body></html>"))
        #self.servo_widget.setGeometry(QRect(440, 70, 131, 326))
        #self.PDH_widget.setGeometry(QRect(300, 70, 131, 236))
        #self.autolock_widget.setGeometry(QRect(20, 70, 131, 257))
        #self.off_widget.setGeometry(QRect(160, 70, 131, 151))
        #self.sls_label.setGeometry(QRect(160, 10, 271, 41))

    def makeLayout(self):
        pass

    def _lock(self, status):
        # get parent
        # disable parent
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SLS_gui)
