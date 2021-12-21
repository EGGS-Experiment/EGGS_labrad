from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QDoubleSpinBox, QComboBox, QGridLayout

from EGGS_labrad.lib.clients.Widgets import TextChangingButton as _TextChangingButton


class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)


class f70_gui(QFrame):
    def __init__(self, parent=None):
        window = QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("F70 Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(350, 400)
        self.all_label = QLabel('F70 Compressor')
        self.all_label.setFont(QFont(shell_font, pointSize=20))
        self.all_label.setAlignment(Qt.AlignCenter)
        # niops03
        self.ip_label = QLabel('Ion Pump')
        self.ip_label.setFont(QFont(shell_font, pointSize=15))
        self.ip_label.setAlignment(Qt.AlignCenter)
            # temperature readout
        self.ip_temperature_display_label = QLabel('Temperature (C)')
        self.ip_temperature_display = QLabel('Temp')
        self.ip_temperature_display.setFont(QFont(shell_font, pointSize=20))
        self.ip_temperature_display.setAlignment(Qt.AlignCenter)
        self.ip_temperature_display.setStyleSheet('color: blue')
            # pressure readout
        self.ip_pressure_display_label = QLabel('Pressure (mbar)')
        self.ip_pressure_display = QLabel('Pressure')
        self.ip_pressure_display.setFont(QFont(shell_font, pointSize=20))
        self.ip_pressure_display.setAlignment(Qt.AlignCenter)
        self.ip_pressure_display.setStyleSheet('color: blue')
            # voltage readout
        self.ip_voltage_display_label = QLabel('Output Voltage (V)')
        self.ip_voltage_display = QLabel('Voltage')
        self.ip_voltage_display.setFont(QFont(shell_font, pointSize=20))
        self.ip_voltage_display.setAlignment(Qt.AlignCenter)
        self.ip_voltage_display.setStyleSheet('color: blue')
            # voltage setting
        self.ip_voltage_label = QLabel('Set Voltage (V)')
        self.ip_voltage = QDoubleSpinBox()
        self.ip_voltage.setFont(QFont(shell_font, pointSize=16))
        self.ip_voltage.setDecimals(0)
        self.ip_voltage.setSingleStep(1)
        self.ip_voltage.setRange(1200, 6000)
        self.ip_voltage.setKeyboardTracking(False)
            # working time
        self.ip_workingtime_display_label = QLabel('Working Time (Hours:Minutes)')
        self.ip_workingtime_display = QLabel('00:00')
        self.ip_workingtime_display.setFont(QFont(shell_font, pointSize=20))
        self.ip_workingtime_display.setAlignment(Qt.AlignCenter)
        self.ip_workingtime_display.setStyleSheet('color: blue')
            # record button
        self.ip_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            # power
        self.ip_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.ip_lockswitch.setChecked(True)
        self.ip_power = TextChangingButton(('On', 'Off'))

        # getter
        self.np_label = QLabel('Getter')
        self.np_label.setFont(QFont(shell_font, pointSize=15))
        self.np_label.setAlignment(Qt.AlignCenter)
            # working time
        self.np_temperature_display_label = QLabel('Temperature (C)')
        self.np_temperature_display = QLabel('Temp')
        self.np_temperature_display.setFont(QFont(shell_font, pointSize=20))
        self.np_temperature_display.setAlignment(Qt.AlignCenter)
        self.np_temperature_display.setStyleSheet('color: blue')
            # mode
        self.np_mode_label = QLabel('Mode')
        self.np_mode = QComboBox()
        self.np_mode.setFont(QFont(shell_font, pointSize=12))
        self.np_mode.addItems(['Activation', 'Timed Activation', 'Conditioning', 'Timed Conditioning'])
            # power
        self.np_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.np_lockswitch.setChecked(True)
        self.np_power = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        layout.addWidget(self.all_label, 0, 0, 1, 2)

        pump1_col = 0
        pump2_col = 1

        layout.addWidget(self.ip_label, 1, pump1_col)
        layout.addWidget(self.ip_pressure_display_label, 2, pump1_col)
        layout.addWidget(self.ip_pressure_display, 3, pump1_col)
        layout.addWidget(self.ip_temperature_display_label, 4, pump1_col)
        layout.addWidget(self.ip_temperature_display, 5, pump1_col)
        layout.addWidget(self.ip_voltage_display_label, 6, pump1_col)
        layout.addWidget(self.ip_voltage_display, 7, pump1_col)
        layout.addWidget(self.ip_voltage_label, 8, pump1_col)
        layout.addWidget(self.ip_voltage, 9, pump1_col)
        layout.addWidget(self.ip_power, 10, pump1_col)
        layout.addWidget(self.ip_lockswitch, 11, pump1_col)
        layout.addWidget(self.ip_record, 12, pump1_col)

        layout.addWidget(self.np_label, 1, pump2_col)
        layout.addWidget(self.np_temperature_display_label, 4, pump2_col)
        layout.addWidget(self.np_temperature_display, 5, pump2_col)
        layout.addWidget(self.np_mode_label, 8, pump2_col)
        layout.addWidget(self.np_mode, 9, pump2_col)
        layout.addWidget(self.np_power, 10, pump2_col)
        layout.addWidget(self.np_lockswitch, 11, pump2_col)

        self.setLayout(layout)


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(f70_gui)
