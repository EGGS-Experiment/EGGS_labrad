from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QGridLayout, QPushButton, QDoubleSpinBox, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox
from EGGS_labrad.clients.utils import SHELL_FONT


class IonizationLaserShutterGUI(QFrame):
    """
    GUI for the laser shutters
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 400)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Ionization Laser Shutters Client")
        self.makeLayout()

    def makeLayout(self):
        font = QFont('MS Shell Dlg 2', pointSize=18)
        layout = QGridLayout(self)

        # title
        title = QLabel("Ionization Laser Shutters Client")
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(self._makeShutterButtons())

    def _makeShutterButtons(self):
        shutter_widget = QWidget()
        shutter_layout = QGridLayout(shutter_widget)

        self.lockswitch = Lockswitch()
        self.lockswitch.setFont(QFont(SHELL_FONT, pointSize=11))
        shutter_layout.addWidget(self.lockswitch)

        self.label_423 = QLabel("423 Shutter")
        self.label_423.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        shutter_layout.addWidget(self.label_423)

        # create modulation frequency subwidget
        self.toggle_423 = TextChangingButton(('Open', 'Closed'), fontsize=10)
        self.toggle_423.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.toggle_423.setFixedSize(200, 100)
        shutter_layout.addWidget(self.toggle_423)


        self.label_377 = QLabel("377 Shutter")
        self.label_377.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        shutter_layout.addWidget(self.label_377)

        # create modulation frequency subwidget
        self.toggle_377 = TextChangingButton(('Open', 'Closed'), fontsize=10)
        self.toggle_377.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.toggle_377.setFixedSize(200,100)
        shutter_layout.addWidget(self.toggle_377)
        return QCustomGroupBox(shutter_widget, "Ionization Laser Shutters")

if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(IonizationLaserShutterGUI)


