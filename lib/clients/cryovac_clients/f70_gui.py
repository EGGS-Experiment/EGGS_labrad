from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QVBoxLayout, QPushButton

from EGGS_labrad.lib.clients.Widgets import TextChangingButton, Lockswitch


class f70_gui(QFrame):
    def __init__(self, parent=None):
        window = QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("F70 Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(350, 500)
        self.all_label = QLabel('F70 Compressor')
        self.all_label.setFont(QFont(shell_font, pointSize=20))
        self.all_label.setAlignment(Qt.AlignCenter)
        # readout
            # temperature readout
        self.temperature_display_label = QLabel('Temperature (C)')
        self.temperature_display = QLabel('Temp')
        self.temperature_display.setFont(QFont(shell_font, pointSize=20))
        self.temperature_display.setAlignment(Qt.AlignCenter)
        self.temperature_display.setStyleSheet('color: blue')
            # pressure readout
        self.pressure_display_label = QLabel('Pressure (psig)')
        self.pressure_display = QLabel('Pressure')
        self.pressure_display.setFont(QFont(shell_font, pointSize=20))
        self.pressure_display.setAlignment(Qt.AlignCenter)
        self.pressure_display.setStyleSheet('color: green')
        # control
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.lockswitch = Lockswitch()
        self.lockswitch.setChecked(True)
        self.power_button = TextChangingButton(('On', 'Off'))
        self.reset_button = QPushButton('Reset')
        self.coldhead_pause = TextChangingButton(('Paused', 'Running'))


    def makeLayout(self):
        layout = QGridLayout()
        layout.addWidget(self.all_label, 0, 0, 1, 2)
        # readouts
        layout.addWidget(self.pressure_display_label, 2, 0)
        layout.addWidget(self.pressure_display, 3, 0)
        layout.addWidget(self.temperature_display_label, 4, 0)
        layout.addWidget(self.temperature_display, 5, 0)
        layout.addWidget(self.voltage_display_label, 6, 0)
        layout.addWidget(self.voltage_display, 7, 0)
        layout.addWidget(self.voltage_label, 8, 0)
        layout.addWidget(self.voltage, 9, 0)
        layout.addWidget(self.power, 10, 0)
        layout.addWidget(self.lockswitch, 11, 0)
        layout.addWidget(self.record, 12, 0)
        end_of_readouts = 10
        # controls
        layout.addWidget(self.power_button, end_of_readouts + 1, 0)
        layout.addWidget(self.coldhead_pause, end_of_readouts + 1, 1)
        layout.addWidget(self.record_button, end_of_readouts + 2, 0)
        layout.addWidget(self.lockswitch, end_of_readouts + 2, 1)
        layout.addWidget(self.reset_button, end_of_readouts + 3, 0)
        self.setLayout(layout)


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(f70_gui)
