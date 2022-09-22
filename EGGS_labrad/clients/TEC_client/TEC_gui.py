from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QDoubleSpinBox, QWidget

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox, Lockswitch


class TEC_gui(QFrame):
    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        #self.setFixedSize(350, 275)
        self.setWindowTitle("TEC Client")
        self.makeWidgets()

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QGridLayout(self)

        # title
        title = QLabel('AMO2 TEC Client')
        title.setFont(QFont(shell_font, pointSize=16))
        title.setAlignment(Qt.AlignCenter)

        # general
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.lock_button = Lockswitch()

        # display
        displayTemp_label = QLabel("Temperature (C)")
        self.displayTemp = QLabel("Temp")
        self.displayTemp.setAlignment(Qt.AlignRight)
        self.displayTemp.setFont(QFont(shell_font, pointSize=24))
        self.displayTemp.setStyleSheet('color: blue')

        displayCurr_label = QLabel("Current (A)")
        self.displayCurr = QLabel("Curr")
        self.displayCurr.setAlignment(Qt.AlignRight)
        self.displayCurr.setFont(QFont(shell_font, pointSize=24))
        self.displayCurr.setStyleSheet('color: blue')

        displayWidget = QWidget()
        displayWidget_layout = QGridLayout(displayWidget)
        displayWidget_layout.addWidget(displayTemp_label, 0, 0, 1, 2)
        displayWidget_layout.addWidget(displayCurr_label, 0, 2, 1, 2)
        displayWidget_layout.addWidget(self.displayTemp, 1, 0, 2, 2)
        displayWidget_layout.addWidget(self.displayCurr, 1, 2, 2, 2)
        displayWidget_grouped = QCustomGroupBox(displayWidget, "Locking")

        # locking
        self.toggle_button = TextChangingButton(('On', 'Off'))
        for widget_name in ("lock_set", "lock_P", "lock_I", "lock_D"):
            widget = QDoubleSpinBox()
            widget.setFont(QFont('MS Shell Dlg 2', pointSize=16))
            widget.setDecimals(0)
            widget.setSingleStep(1)
            widget.setRange(0, 255)
            widget.setKeyboardTracking(False)
            widget.setAlignment(Qt.AlignRight)
            setattr(self, widget_name, widget)

        lock_set_label = QLabel("Setpoint (C)")
        lock_P_label = QLabel("Prop.")
        lock_I_label = QLabel("Int.")
        lock_D_label = QLabel("Deriv.")

        # adjust range for setpoint
        self.lock_set.setRange(10, 35)

        lockingWidget = QWidget()
        lockingWidget_layout = QGridLayout(lockingWidget)
        lockingWidget_layout.addWidget(lock_set_label, 0, 3, 1, 3)
        lockingWidget_layout.addWidget(self.toggle_button, 1, 0, 1, 3)
        lockingWidget_layout.addWidget(self.lock_set, 1, 3, 1, 3)
        lockingWidget_layout.addWidget(lock_P_label, 2, 0, 1, 2)
        lockingWidget_layout.addWidget(lock_I_label, 2, 2, 1, 2)
        lockingWidget_layout.addWidget(lock_D_label, 2, 4, 1, 2)
        lockingWidget_layout.addWidget(self.lock_P, 3, 0, 1, 2)
        lockingWidget_layout.addWidget(self.lock_I, 3, 2, 1, 2)
        lockingWidget_layout.addWidget(self.lock_D, 3, 4, 1, 2)
        lockingWidget_grouped = QCustomGroupBox(lockingWidget, "Status")

        # layout
        layout.addWidget(title, 1, 0, 1, 4)
        layout.addWidget(displayWidget_grouped, 2, 0, 3, 4)
        layout.addWidget(lockingWidget_grouped, 5, 0, 3, 4)
        layout.addWidget(self.record_button, 8, 0, 1, 2)
        layout.addWidget(self.lock_button, 8, 2, 1, 2)

    def _lock(self, status):
        self.toggle_button.setEnabled(status)
        self.record_button.setEnabled(status)
        self.lock_set.setEnabled(status)
        self.lock_P.setEnabled(status)
        self.lock_I.setEnabled(status)
        self.lock_D.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(TEC_gui)
