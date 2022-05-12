from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QClientMenuHeader


class twistorr74_gui(QFrame):
    def __init__(self, parent=None):
        window = QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Twistorr74 Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.setMinimumSize(280, 370)
        self.setMaximumSize(300, 400)
        # label
        self.twistorr_label = QLabel('Twistorr 74 Pump')
        self.twistorr_label.setFont(QFont(shell_font, pointSize=18))
        self.twistorr_label.setAlignment(Qt.AlignCenter)
        # pressure readout
        self.pressure_display_label = QLabel('Pressure (mbar)')
        self.pressure_display = QLabel('Pressure')
        self.pressure_display.setFont(QFont(shell_font, pointSize=20))
        self.pressure_display.setAlignment(Qt.AlignCenter)
        self.pressure_display.setStyleSheet('color: blue')
        # power readout
        self.power_display_label = QLabel('Power (W)')
        self.power_display = QLabel('Power')
        self.power_display.setFont(QFont(shell_font, pointSize=20))
        self.power_display.setAlignment(Qt.AlignCenter)
        self.power_display.setStyleSheet('color: blue')
        # speed readout
        self.speed_display_label = QLabel('Speed (Hz)')
        self.speed_display = QLabel('Speed')
        self.speed_display.setFont(QFont(shell_font, pointSize=20))
        self.speed_display.setAlignment(Qt.AlignCenter)
        self.speed_display.setStyleSheet('color: blue')
        # record button
        self.twistorr_record = TextChangingButton(('Stop Recording', 'Start Recording'))
        # power
        self.twistorr_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.twistorr_lockswitch.toggled.connect(lambda status: self._lock(status))
        self.twistorr_toggle = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QGridLayout(self)
        shell_font = 'MS Shell Dlg 2'
        self.header = QClientMenuHeader()

        row1, col1 = (0, 0)
        layout.setMenuBar(self.header)
        layout.addWidget(self.twistorr_label,           0 + row1, col1, 1, 1)
        layout.addWidget(self.pressure_display_label,   1 + row1, col1)
        layout.addWidget(self.pressure_display,         2 + row1, col1)
        layout.addWidget(self.power_display_label,      3 + row1, col1)
        layout.addWidget(self.power_display,            4 + row1, col1)
        layout.addWidget(self.speed_display_label,      5 + row1, col1)
        layout.addWidget(self.speed_display,            6 + row1, col1)
        layout.addWidget(self.twistorr_toggle,          7 + row1, col1)
        layout.addWidget(self.twistorr_lockswitch,      8 + row1, col1)
        layout.addWidget(self.twistorr_record,          9 + row1, col1)
        # layout.minimumSize()

    def _lock(self, status):
        """
        Lock everything except the Lockswitch.
        """
        self.twistorr_toggle.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(twistorr74_gui)