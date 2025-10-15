from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QGridLayout, QAbstractSpinBox

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox, QCustomUnscrollableSpinBox
from EGGS_labrad.clients.utils import SHELL_FONT


class InjectionLockCurrentGUI(QFrame):
    """
    GUI for the diode controller for the 729 diode
    """
    MAX_CURRENT = 100.01

    def __init__(self):
        super().__init__()
        # self.setFixedSize(500, 400)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Injection Lock Current Client")
        self.makeLayout()

    def makeLayout(self):
        font = QFont('MS Shell Dlg 2', pointSize=18)
        layout = QGridLayout(self)

        # title
        title = QLabel("Injection Lock Current Client")
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.makeButtons())

    def makeButtons(self):
        injection_lock_current_widget = QWidget()
        injection_lock_current_layout = QGridLayout(injection_lock_current_widget)

        self.lockswitch = Lockswitch()
        self.lockswitch.setFont(QFont(SHELL_FONT, pointSize=12))
        injection_lock_current_layout.addWidget(self.lockswitch, 0, 0, 1, 4)

        self.output_button = TextChangingButton(("On", "Off"), fontsize=12)
        injection_lock_current_layout.addWidget(self.output_button, 1,0,1,4)

        displayCurr_label = QLabel("Diode Current (mA)")
        displayCurr_label.setFont(QFont(SHELL_FONT, pointSize=12))
        injection_lock_current_layout.addWidget(displayCurr_label, 2, 0, 1, 2)
        self.label_diode_current = QLabel("Curr")
        self.label_diode_current.setAlignment(Qt.AlignCenter)
        self.label_diode_current.setFont(QFont('MS Shell Dlg 2', pointSize=24))
        injection_lock_current_layout.addWidget(self.label_diode_current, 3,0, 2,2)


        displayVoltage_label = QLabel("Diode Voltage (V)")
        displayVoltage_label.setFont(QFont(SHELL_FONT, pointSize=12))
        injection_lock_current_layout.addWidget(displayVoltage_label, 2, 2, 1, 2)
        self.label_diode_voltage = QLabel("Volt")
        self.label_diode_voltage.setAlignment(Qt.AlignCenter)
        self.label_diode_voltage.setFont(QFont('MS Shell Dlg 2', pointSize=24))
        injection_lock_current_layout.addWidget(self.label_diode_voltage, 3,2, 2,2)

        self.label_set_current = QLabel("Set Current (mA)")
        self.label_set_current.setAlignment(Qt.AlignCenter)
        self.label_set_current.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        injection_lock_current_layout.addWidget(self.label_set_current, 5,0, 1,1)

        # create set current subwidget
        self.set_current_spinbox = QCustomUnscrollableSpinBox(self)
        self.set_current_spinbox.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        # self.set_current_spinbox.setFixedSize(200, 100)
        self.set_current_spinbox.setDecimals(3)
        self.set_current_spinbox.setSingleStep(0.001)
        self.set_current_spinbox.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.set_current_spinbox.setMaximum(self.MAX_CURRENT)
        # self.set_current_spinbox.setValue(97.475)
        injection_lock_current_layout.addWidget(self.set_current_spinbox, 6, 0, 2, 2)

        # create max current button
        self.label_max_current = QLabel("Max Current (mA)")
        self.label_max_current.setAlignment(Qt.AlignCenter)
        self.label_max_current.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        injection_lock_current_layout.addWidget(self.label_max_current, 5, 2, 1, 1)

        # create set current subwidget
        self.max_current_spinbox = QCustomUnscrollableSpinBox(self)
        self.max_current_spinbox.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        # self.max_current_spinbox.setFixedSize(200, 100)
        self.max_current_spinbox.setDecimals(3)
        self.max_current_spinbox.setSingleStep(0.001)
        self.max_current_spinbox.setMaximum(self.MAX_CURRENT)
        # self.max_current_spinbox.setValue(100.)
        self.max_current_spinbox.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        injection_lock_current_layout.addWidget(self.max_current_spinbox, 6, 2, 2, 2)

        return QCustomGroupBox(injection_lock_current_widget, "Injection Lock Current")


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(InjectionLockCurrentGUI)