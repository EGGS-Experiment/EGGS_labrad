from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QGridLayout, QPushButton, QDoubleSpinBox, \
QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox
from EGGS_labrad.clients.utils import SHELL_FONT


class InjectionLockDiodeGUI(QFrame):
    """
    GUI for the injection lock diode client
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 400)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Injection Lock Diode")
        self.makeLayout()

    def makeLayout(self):
        font = QFont('MS Shell Dlg 2', pointSize=18)
        layout = QGridLayout(self)

        # title
        title = QLabel("Injection Lock Diode Client")
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.makeInjectionLockDiodeCurrentWidget(), 0, 1, 1, 1)
        layout.addWidget(self.makeInjectionLockDiodeTempWidget(), 0, 0, 1, 1)

    def makeInjectionLockDiodeCurrentWidget(self):

        current_widget = QWidget()
        current_layout = QGridLayout(current_widget)

        self.lockswitch = Lockswitch()
        self.lockswitch.setFont(QFont(SHELL_FONT, pointSize=11))
        current_layout.addWidget(self.lockswitch)

        self.label_current = QLabel("Diode Current (mA)")
        self.label_current.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        current_layout.addWidget(self.label_current)

        # create modulation frequency subwidget
        self.current = QDoubleSpinBox()
        self.current.setRange(1, 100)
        self.current.setDecimals(3)
        self.current.setSingleStep(0.01)
        self.current.setFixedSize(200, 100)
        current_layout.addWidget(self.current)
        return QCustomGroupBox(current_widget, "Injection Lock Diode Current")


    def makeInjectionLockDiodeTempWidget(self):

        current_widget = QWidget()
        current_layout = QGridLayout(current_widget)

        self.lockswitch = Lockswitch()
        self.lockswitch.setFont(QFont(SHELL_FONT, pointSize=11))
        current_layout.addWidget(self.lockswitch)

        self.label_current = QLabel("Diode Temperature (C)")
        self.label_current.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        current_layout.addWidget(self.label_current)

        return QCustomGroupBox(current_widget, "Injection Lock Diode Current")


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(InjectionLockDiodeGUI)


