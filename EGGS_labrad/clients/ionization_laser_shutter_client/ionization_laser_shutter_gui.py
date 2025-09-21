from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QGridLayout, QPushButton, QDoubleSpinBox, QVBoxLayout
)

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox


class IonizationLaserShutterGUI(QFrame):
    """
    GUI for the laser shutters.
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(225, 325)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Ionization Laser Shutters Client")
        self.makeLayout()

    def makeLayout(self):
        # create parent layout
        layout = QGridLayout(self)

        # title
        title = QLabel("Ionization Laser Shutters Client")
        title.setFont(QFont(SHELL_FONT, pointSize=18))
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(self._makeShutterButtons())

    def _makeShutterButtons(self):
        # prepare widget layout
        shutter_widget = QWidget()
        shutter_layout = QGridLayout(shutter_widget)

        # lockswitch (disable user input)
        self.lockswitch = Lockswitch()
        self.lockswitch.setFont(QFont(SHELL_FONT, pointSize=11))
        shutter_layout.addWidget(self.lockswitch)

        # create shutter button - 423nm
        self.label_423 = QLabel("423nm Shutter")
        self.label_423.setFont(QFont(SHELL_FONT, pointSize=10))
        shutter_layout.addWidget(self.label_423)

        self.toggle_423 = TextChangingButton(('OPEN', 'CLOSED'), fontsize=12)
        self.toggle_423.setFixedSize(140, 70)
        shutter_layout.addWidget(self.toggle_423)

        # create shutter button - 375nm
        self.label_377 = QLabel("377nm Shutter")
        self.label_377.setFont(QFont(SHELL_FONT, pointSize=10))
        shutter_layout.addWidget(self.label_377)

        self.toggle_377 = TextChangingButton(('OPEN', 'CLOSED'), fontsize=12)
        self.toggle_377.setFixedSize(140, 70)
        shutter_layout.addWidget(self.toggle_377)

        _grouped_widget = QCustomGroupBox(shutter_widget, "Ionization Laser Shutters")
        _grouped_widget.setFont(QFont(SHELL_FONT, pointSize=9))
        return _grouped_widget


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(IonizationLaserShutterGUI)

