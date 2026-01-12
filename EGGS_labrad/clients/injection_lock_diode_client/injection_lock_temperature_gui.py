from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QWidget

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox, Lockswitch, QCustomUnscrollableSpinBox


class InjectionLockTemperatureGUI(QFrame):
    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("TEC Client")
        self.makeLayout()
        self.setMinimumSize(295, 340)

    def makeLayout(self):
        layout = QGridLayout(self)

        # title
        title = QLabel('Injection Lock TEC Client')
        title.setFont(QFont(SHELL_FONT, pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        # general
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.lock_button = Lockswitch()

        # lay out overall widget
        layout.addWidget(title,                     0, 0, 1, 4)
        layout.addWidget(self._makeStatusWidget(),  1, 0, 3, 4)
        layout.addWidget(self._makeLockingWidget(), 4, 0, 3, 4)
        layout.addWidget(self.record_button,        7, 0, 1, 2)
        layout.addWidget(self.lock_button,          7, 2, 1, 2)

    def _makeStatusWidget(self):
        # display
        displayTemp_label = QLabel("Temperature (C)")
        self.displayTemp = QLabel("Temp")
        self.displayTemp.setAlignment(Qt.AlignRight)
        self.displayTemp.setFont(QFont(SHELL_FONT, pointSize=20))
        self.displayTemp.setStyleSheet('color: blue')

        displayCurr_label = QLabel("Current (A)")
        self.displayCurr = QLabel("Curr")
        self.displayCurr.setAlignment(Qt.AlignRight)
        self.displayCurr.setFont(QFont(SHELL_FONT, pointSize=20))
        self.displayCurr.setStyleSheet('color: blue')

        displayWidget = QWidget()
        displayWidget_layout = QGridLayout(displayWidget)
        displayWidget_layout.addWidget(displayTemp_label,   0, 0, 1, 2)
        displayWidget_layout.addWidget(self.displayTemp,    1, 0, 2, 2)
        displayWidget_layout.addWidget(displayCurr_label,   0, 2, 1, 2)
        displayWidget_layout.addWidget(self.displayCurr,    1, 2, 2, 2)
        return QCustomGroupBox(displayWidget, "Status")

    def _makeLockingWidget(self):
        # create relevant labels
        output_label =      QLabel("Output")
        lock_set_label =    QLabel("Setpoint (C)")
        lock_P_label =      QLabel("Prop.")
        lock_I_label =      QLabel("Int.")
        lock_D_label =      QLabel("Deriv.")

        # create output button
        self.toggle_button = TextChangingButton(('On', 'Off'))
        self.toggle_button.setFont(QFont('MS Shell Dlg 2', pointSize=15))

        # programmatically create widgets for PID
        for widget_name in ("lock_set", "lock_P", "lock_I", "lock_D"):
            widget = QCustomUnscrollableSpinBox()
            widget.setFont(QFont('MS Shell Dlg 2', pointSize=15))
            widget.setDecimals(0)
            widget.setSingleStep(1)
            widget.setRange(0, 255)
            widget.setKeyboardTracking(False)
            widget.setAlignment(Qt.AlignRight)
            setattr(self, widget_name, widget)
        # extra configuration for the setpoint
        self.lock_set.setRange(10, 35)
        self.lock_set.setDecimals(3)
        self.lock_set.setSingleStep(0.005)

        # lay out locking widget
        lockingWidget = QWidget()
        lockingWidget_layout = QGridLayout(lockingWidget)
        lockingWidget_layout.addWidget(lock_set_label,      0, 3, 1, 3)
        lockingWidget_layout.addWidget(self.lock_set,       1, 3, 1, 3)
        lockingWidget_layout.addWidget(output_label,        0, 0, 1, 3)
        lockingWidget_layout.addWidget(self.toggle_button,  1, 0, 1, 3)
        lockingWidget_layout.addWidget(lock_P_label,        2, 0, 1, 2)
        lockingWidget_layout.addWidget(self.lock_P,         3, 0, 1, 2)
        lockingWidget_layout.addWidget(lock_I_label,        2, 2, 1, 2)
        lockingWidget_layout.addWidget(self.lock_I,         3, 2, 1, 2)
        lockingWidget_layout.addWidget(lock_D_label,        2, 4, 1, 2)
        lockingWidget_layout.addWidget(self.lock_D,         3, 4, 1, 2)
        return QCustomGroupBox(lockingWidget, "Locking")

    def _lock(self, status):
        self.toggle_button.setEnabled(status)
        self.record_button.setEnabled(status)
        self.lock_set.setEnabled(status)
        self.lock_P.setEnabled(status)
        self.lock_I.setEnabled(status)
        self.lock_D.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(InjectionLockTemperatureGUI)
