from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch


class f70_gui(QFrame):
    def __init__(self, parent=None):
        window = QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("F70 Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(300, 420)
        self.all_label = QLabel('F70 Compressor')
        self.all_label.setFont(QFont(shell_font, pointSize=18))
        self.all_label.setAlignment(Qt.AlignCenter)
        # readout
            # temperature readout
        self.temperature_display = QWidget(self)
        self.temperature_display_layout = QGridLayout(self.temperature_display)
        self.temperature_display_label = QLabel('Temperature (C)')
        self.temperature_display_label.setFont(QFont(shell_font, pointSize=14))
        self.temperature_display_layout.addWidget(self.temperature_display_label, 0, 0, 1, 2)
        self.temperature_display_channel_labels = [QLabel("Helium discharge"), QLabel("Water outlet"),
                                                   QLabel("Water inlet"), QLabel("Other")]
        self.temperature_display_channels = [QLabel("Temp1"), QLabel("Temp2"),
                                             QLabel("Temp3"), QLabel("Temp4")]
        for i in range(4):
            channel = self.temperature_display_channels[i]
            channel_label = self.temperature_display_channel_labels[i]
            channel.setFont(QFont(shell_font, pointSize=20))
            channel.setAlignment(Qt.AlignCenter)
            channel.setStyleSheet('color: blue')
            row = int(i / 2) * 2 + 1
            col = i % 2
            self.temperature_display_layout.addWidget(channel_label, row, col)
            self.temperature_display_layout.addWidget(channel, row + 1, col)

            # pressure readout
        self.pressure_display = QWidget(self)
        self.pressure_display_layout = QGridLayout(self.pressure_display)
        self.pressure_display_label = QLabel('Pressure (psig)')
        self.pressure_display_label.setFont(QFont(shell_font, pointSize=14))
        self.pressure_display_layout.addWidget(self.pressure_display_label, 0, 0, 1, 2)
        self.pressure_display_channel_1_label = QLabel("Compressor return")
        self.pressure_display_channel_1 = QLabel("Press1")
        self.pressure_display_channel_1.setFont(QFont(shell_font, pointSize=20))
        self.pressure_display_channel_1.setAlignment(Qt.AlignCenter)
        self.pressure_display_channel_1.setStyleSheet('color: green')
        self.pressure_display_layout.addWidget(self.pressure_display_channel_1_label, 1, 0)
        self.pressure_display_layout.addWidget(self.pressure_display_channel_1, 2, 0)
        self.pressure_display_channel_2_label = QLabel("Other")
        self.pressure_display_channel_2 = QLabel("Press2")
        self.pressure_display_channel_2.setFont(QFont(shell_font, pointSize=20))
        self.pressure_display_channel_2.setAlignment(Qt.AlignCenter)
        self.pressure_display_channel_2.setStyleSheet('color: green')
        self.pressure_display_layout.addWidget(self.pressure_display_channel_2_label, 1, 1)
        self.pressure_display_layout.addWidget(self.pressure_display_channel_2, 2, 1)
        # control
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.record_button.setFixedHeight(23)
        self.record_button.setFont(QFont(shell_font, pointSize=8))
        self.lockswitch = Lockswitch()
        self.lockswitch.setChecked(True)
        self.power_button = TextChangingButton(('On', 'Off'))
        self.power_button.setFixedHeight(23)
        self.power_button.setFont(QFont(shell_font, pointSize=8))
        self.coldhead_pause = TextChangingButton(('Paused', 'Running'))
        self.coldhead_pause.setFixedHeight(23)
        self.coldhead_pause.setFont(QFont(shell_font, pointSize=8))
        self.reset_button = QPushButton('Reset')

    def makeLayout(self):
        layout = QGridLayout()
        layout.addWidget(self.all_label, 0, 0, 1, 2)
        # readouts
        layout.addWidget(self.temperature_display, 2, 0, 3, 2)
        layout.addWidget(self.pressure_display, 6, 0, 3, 2)
        end_of_readouts = 9
        # controls
        layout.addWidget(self.power_button, end_of_readouts + 1, 0)
        layout.addWidget(self.coldhead_pause, end_of_readouts + 1, 1)
        layout.addWidget(self.record_button, end_of_readouts + 2, 0)
        layout.addWidget(self.lockswitch, end_of_readouts + 2, 1)
        layout.addWidget(self.reset_button, end_of_readouts + 3, 0)
        self.setLayout(layout)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(f70_gui)
