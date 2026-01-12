from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QVBoxLayout

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import (TextChangingButton, QCustomGroupBox,
                                         QCustomUnscrollableSpinBox, QCustomUnscrollableComboBox)
# todo: condense


class SLS_gui(QFrame):

    def __init__(self, channelinfo=None):
        super().__init__()
        self.setWindowTitle('SLS Client')
        self.setFrameStyle(0x0001 | 0x0030)
        # self.setFixedSize(680, 410)
        self.makeLayout()
        for widget in (self.autolock_lockswitch, self.offset_lockswitch,
                       self.PDH_lockswitch, self.servo_lockswitch):
            widget.setChecked(False)

    def _makeAutolockWidget(self):
        autolock_widget = QWidget(self)
        autolock_layout = QVBoxLayout(autolock_widget)

        autolock_param_label = QLabel("Sweep Parameter")
        autolock_param_label.setFont(QFont(SHELL_FONT, 16))
        autolock_toggle_label = QLabel("Autolock")
        autolock_toggle_label.setFont(QFont(SHELL_FONT, 16))
        autolock_attempts_label = QLabel("Lock Attempts")
        autolock_attempts_label.setFont(QFont(SHELL_FONT, 16))
        autolock_status_label = QLabel("Autolock Status")
        autolock_status_label.setFont(QFont(SHELL_FONT, 16))

        self.autolock_param = QCustomUnscrollableComboBox()
        self.autolock_param.addItems(["Off", "PZT", "Current"])
        self.autolock_param.setFont(QFont(SHELL_FONT, 16))

        self.autolock_attempts = QLabel("NULL")
        self.autolock_attempts.setAlignment(Qt.AlignCenter)
        self.autolock_attempts.setFont(QFont(SHELL_FONT, pointSize=16))
        self.autolock_attempts.setStyleSheet('color: blue')

        self.autolock_status = QLabel("FALSE")
        self.autolock_status.setAlignment(Qt.AlignCenter)
        self.autolock_status.setFont(QFont(SHELL_FONT, pointSize=16))
        self.autolock_status.setStyleSheet('color: blue')
        self.autolock_toggle = TextChangingButton(('On', 'Off'))
        self.autolock_toggle.setFont(QFont(SHELL_FONT, pointSize=16))

        for widget in (autolock_attempts_label, self.autolock_attempts,
                       autolock_status_label, self.autolock_status,
                       autolock_toggle_label, self.autolock_toggle,
                       autolock_param_label, self.autolock_param):
            autolock_layout.addWidget(widget)
        return QCustomGroupBox(autolock_widget, "Autolock")

    def _makeOffsetWidget(self):
        offset_widget = QWidget()
        offset_layout = QVBoxLayout(offset_widget)

        offset_lockpoint_label = QLabel("Lockpoint")
        offset_lockpoint_label.setFont(QFont(SHELL_FONT, 16))
        offset_eom_rf_amp_label = QLabel("EOM RF Amplitude")
        offset_eom_rf_amp_label.setFont(QFont(SHELL_FONT, 16))
        offset_freq_label = QLabel("Offset Frequency (MHz)")
        offset_freq_label.setFont(QFont(SHELL_FONT, 16))

        offset_buttons = {
            'offset_freq': (10.0, 800.0, 1.0),
            'offset_eom_rf_amp': (0,100.0, 0.1)
        }
        for offset_button_name, button_vals in offset_buttons.items():
            setattr(self, offset_button_name, QCustomUnscrollableSpinBox())
            offset_button = getattr(self, offset_button_name)
            offset_button.setRange(button_vals[0], button_vals[1])
            offset_button.setSingleStep(button_vals[2])

            offset_font = offset_button.font()
            offset_font.setPointSize(16)
            offset_button.setFont(offset_font)

        self.offset_lockpoint = QCustomUnscrollableComboBox()
        self.offset_lockpoint.addItems(["J(+2)", "J(+1)", "Resonance", "J(-1)", "J(-2)"])
        self.offset_lockpoint.setFont(QFont(SHELL_FONT, pointSize=16))

        for widget in (offset_freq_label, self.offset_freq,
                       offset_eom_rf_amp_label, self.offset_eom_rf_amp,
                       offset_lockpoint_label, self.offset_lockpoint):
            offset_layout.addWidget(widget)
        return QCustomGroupBox(offset_widget, "Offset Lock")

    def _makePDHWidget(self):
        pdh_widget = QWidget()
        pdh_layout = QVBoxLayout(pdh_widget)

        pdh_filter_label = QLabel("Filter Index")
        pdh_filter_label.setFont(QFont(SHELL_FONT, 16))
        pdh_phasemodulation_label = QLabel("Phase modulation (rad)")
        pdh_phasemodulation_label.setFont(QFont(SHELL_FONT, 16))
        pdh_phaseoffset_label = QLabel("Reference phase (deg)")
        pdh_phaseoffset_label.setFont(QFont(SHELL_FONT, 16))
        pdh_freq_label = QLabel("Frequency (MHz)")
        pdh_freq_label.setFont(QFont(SHELL_FONT, 16))

        pdh_buttons = {
            'pdh_freq': (10.0, 35.0, 0.1),
            'pdh_phaseoffset': (0, 360.0, 0.1),
            'pdh_phasemodulation': (0, 3.0, 0.1)
        }
        for pdh_button_name, button_vals in pdh_buttons.items():
            setattr(self, pdh_button_name, QCustomUnscrollableSpinBox())
            pdh_button = getattr(self, pdh_button_name)
            pdh_button.setRange(button_vals[0], button_vals[1])
            pdh_button.setSingleStep(button_vals[2])

            pdh_font = pdh_button.font()
            pdh_font.setPointSize(16)
            pdh_button.setFont(pdh_font)

        self.pdh_filter = QCustomUnscrollableComboBox()
        self.pdh_filter.addItems(["None"] + [str(val) for val in range(1,16)])
        self.pdh_filter.setFont(QFont(SHELL_FONT, pointSize=16))

        for widget in (pdh_freq_label, self.pdh_freq,
                       pdh_phasemodulation_label, self.pdh_phasemodulation,
                       pdh_phaseoffset_label, self.pdh_phaseoffset,
                       pdh_filter_label, self.pdh_filter):
            pdh_layout.addWidget(widget)
        return QCustomGroupBox(pdh_widget, "PDH")

    def _makeServoWidget(self):
        servo_widget = QWidget(self)
        servo_layout = QVBoxLayout(servo_widget)

        servo_param_label = QLabel("Parameter")
        servo_param_label.setFont(QFont(SHELL_FONT, 16))
        servo_set_label = QLabel("Setpoint")
        servo_set_label.setFont(QFont(SHELL_FONT,16))
        servo_p_label = QLabel("Proportional")
        servo_p_label.setFont(QFont(SHELL_FONT, 16))
        servo_i_label = QLabel("Integral")
        servo_i_label.setFont(QFont(SHELL_FONT, 16))
        servo_d_label = QLabel("Differential")
        servo_d_label.setFont(QFont(SHELL_FONT, 16))
        servo_filter_label = QLabel("Filter Index")
        servo_filter_label.setFont(QFont(SHELL_FONT, 16))

        self.servo_filter = QCustomUnscrollableComboBox()
        self.servo_filter.addItems(["None"] + [str(val) for val in range(1,16)])
        self.servo_filter.setFont(QFont(SHELL_FONT, pointSize=16))

        servo_buttons = {
            'servo_set': (-1e6, 1e6, 1.),
            'servo_p': (0, 1e3, 1.),
            'servo_i': (0, 1.0, 1e-2),
            'servo_d': (0., 1e3, 1.)
        }
        for servo_button_name, button_vals in servo_buttons.items():
            setattr(self, servo_button_name, QCustomUnscrollableSpinBox())
            servo_button = getattr(self, servo_button_name)
            servo_button.setRange(button_vals[0], button_vals[1])
            servo_button.setSingleStep(button_vals[2])

            servo_font = servo_button.font()
            servo_font.setPointSize(16)
            servo_button.setFont(servo_font)

        self.servo_param = QCustomUnscrollableComboBox()
        self.servo_param.addItems(["Current", "PZT", "TX"])
        self.servo_param.setFont(QFont(SHELL_FONT, 16))

        for widget in (servo_param_label, self.servo_param, servo_set_label, self.servo_set,
                       servo_p_label, self.servo_p, servo_i_label, self.servo_i,
                       servo_d_label, self.servo_d, servo_filter_label, self.servo_filter):
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
        sls_label.setFont(QFont(SHELL_FONT, pointSize=20))
        sls_label.setAlignment(Qt.AlignCenter)

        # lay out
        layout = QGridLayout(self)
        layout.addWidget(sls_label,                 0, 0, 1, 7)
        layout.addWidget(self.autolock_lockswitch,  1, 0, 1, 4)
        layout.addWidget(self.autolock_widget,      2, 0, 7, 4)
        layout.addWidget(self.offset_lockswitch,    1, 4, 1, 1)
        layout.addWidget(self.offset_widget,        2, 4, 4, 1)
        layout.addWidget(self.PDH_lockswitch,       1, 5, 1, 1)
        layout.addWidget(self.PDH_widget,           2, 5, 6, 1)
        layout.addWidget(self.servo_lockswitch,     1, 6, 1, 1)
        layout.addWidget(self.servo_widget,         2, 6, 10, 1)

    def _lock(self, status, widget):
        widget.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SLS_gui)
