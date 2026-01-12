from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QGridLayout

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox, QCustomUnscrollableSpinBox

MAX_CURRENT = 100.01


class InjectionLockCurrentGUI(QFrame):
    """
    GUI for the diode controller for the 729 diode
    """

    def __init__(self):
        super().__init__()
        # self.setFixedSize(500, 400)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Injection Lock Current Client")
        self.makeLayout()

    def makeLayout(self):
        layout = QGridLayout(self)

        # title
        title = QLabel("Injection Lock Current Client")
        title.setFont(QFont(SHELL_FONT, pointSize=15))
        title.setAlignment(Qt.AlignCenter)

        # widgets
        layout.addWidget(title,                 0, 0, 1, 1)
        layout.addWidget(self._makeButtons(),   1, 0, 1, 1)

    def _makeButtons(self):
        injection_lock_current_widget = QWidget()
        injection_lock_current_layout = QGridLayout(injection_lock_current_widget)

        # GENERAL
        self.lockswitch = Lockswitch()
        self.lockswitch.setFont(QFont(SHELL_FONT, pointSize=12))
        self.output_button = TextChangingButton(("On", "Off"), fontsize=14)


        # DISPLAYS
        displayCurr_label = QLabel("Actual Current (mA)")
        displayCurr_label.setFont(QFont(SHELL_FONT, pointSize=12))
        self.label_diode_current = QLabel("00.000")
        self.label_diode_current.setAlignment(Qt.AlignRight)
        self.label_diode_current.setFont(QFont(SHELL_FONT, pointSize=24))

        displayVoltage_label = QLabel("Actual Voltage (V)")
        displayVoltage_label.setFont(QFont(SHELL_FONT, pointSize=12))
        self.label_diode_voltage = QLabel("00.000")
        self.label_diode_voltage.setAlignment(Qt.AlignRight)
        self.label_diode_voltage.setFont(QFont(SHELL_FONT, pointSize=24))


        # CURRENT CONFIG
        # create set current buton
        label_set_current = QLabel("Set Current (mA)")
        label_set_current.setAlignment(Qt.AlignCenter)
        label_set_current.setFont(QFont(SHELL_FONT, pointSize=12))
        # create set current subwidget
        self.set_current_spinbox = QCustomUnscrollableSpinBox(self)
        self.set_current_spinbox.setFont(QFont(SHELL_FONT, pointSize=15))
        self.set_current_spinbox.setDecimals(3)
        self.set_current_spinbox.setSingleStep(0.001)
        self.set_current_spinbox.setRange(0., MAX_CURRENT)
        self.set_current_spinbox.setAlignment(Qt.AlignRight)
        self.set_current_spinbox.setKeyboardTracking(False)

        # create max current label
        label_max_current = QLabel("Max Current (mA)")
        label_max_current.setAlignment(Qt.AlignCenter)
        label_max_current.setFont(QFont(SHELL_FONT, pointSize=12))
        # create max current subwidget
        self.max_current_spinbox = QCustomUnscrollableSpinBox(self)
        self.max_current_spinbox.setFont(QFont(SHELL_FONT, pointSize=15))
        self.max_current_spinbox.setDecimals(3)
        self.max_current_spinbox.setSingleStep(0.001)
        self.max_current_spinbox.setRange(0., MAX_CURRENT)
        self.max_current_spinbox.setAlignment(Qt.AlignRight)
        self.max_current_spinbox.setKeyboardTracking(False)

        # lay out widgets
        injection_lock_current_layout.addWidget(self.output_button,         0, 0, 1, 4)
        injection_lock_current_layout.addWidget(displayCurr_label,          1, 0, 1, 2)
        injection_lock_current_layout.addWidget(self.label_diode_current,   2, 0, 2, 2)
        injection_lock_current_layout.addWidget(displayVoltage_label,       1, 2, 1, 2)
        injection_lock_current_layout.addWidget(self.label_diode_voltage,   2, 2, 2, 2)
        injection_lock_current_layout.addWidget(label_set_current,          4, 0, 1, 1)
        injection_lock_current_layout.addWidget(self.set_current_spinbox,   5, 0, 2, 2)
        injection_lock_current_layout.addWidget(label_max_current,          4, 2, 1, 1)
        injection_lock_current_layout.addWidget(self.max_current_spinbox,   5, 2, 2, 2)
        injection_lock_current_layout.addWidget(self.lockswitch,            7, 0, 1, 4)
        return injection_lock_current_widget


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(InjectionLockCurrentGUI)
