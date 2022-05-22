from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QDoubleSpinBox, QComboBox, QGridLayout, QWidget, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QClientMenuHeader, QCustomGroupBox
_SHELL_FONT = 'MS Shell Dlg 2'

class niops03_gui(QFrame):

    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(350, 445)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("NIOPS03 Client")

    def _makeIPwidget(self):
        ip_widget = QWidget()
        ip_widget_layout = QVBoxLayout(ip_widget)
        # temperature readout
        ip_temperature_display_label = QLabel('Temperature (C)')
        self.ip_temperature_display = QLabel('Temp')
        self.ip_temperature_display.setFont(QFont(_SHELL_FONT, pointSize=20))
        self.ip_temperature_display.setAlignment(Qt.AlignCenter)
        self.ip_temperature_display.setStyleSheet('color: blue')
        # pressure readout
        ip_pressure_display_label = QLabel('Pressure (mbar)')
        self.ip_pressure_display = QLabel('Pressure')
        self.ip_pressure_display.setFont(QFont(_SHELL_FONT, pointSize=20))
        self.ip_pressure_display.setAlignment(Qt.AlignCenter)
        self.ip_pressure_display.setStyleSheet('color: blue')
        # voltage readout
        ip_voltage_display_label = QLabel('Output Voltage (V)')
        self.ip_voltage_display = QLabel('Voltage')
        self.ip_voltage_display.setFont(QFont(_SHELL_FONT, pointSize=20))
        self.ip_voltage_display.setAlignment(Qt.AlignCenter)
        self.ip_voltage_display.setStyleSheet('color: blue')
        # voltage setting
        ip_voltage_label = QLabel('Set Voltage (V)')
        self.ip_voltage = QDoubleSpinBox()
        self.ip_voltage.setFont(QFont(_SHELL_FONT, pointSize=16))
        self.ip_voltage.setDecimals(0)
        self.ip_voltage.setSingleStep(1)
        self.ip_voltage.setRange(1200, 6000)
        self.ip_voltage.setKeyboardTracking(False)
        # record button
        self.ip_record = TextChangingButton(('Stop Recording', 'Start Recording'))
        # power
        self.ip_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.ip_lockswitch.setChecked(True)
        self.ip_power = TextChangingButton(('On', 'Off'))
        # lay out ion pump
        ip_widget_layout.addWidget(ip_pressure_display_label)
        ip_widget_layout.addWidget(self.ip_pressure_display)
        ip_widget_layout.addWidget(ip_temperature_display_label)
        ip_widget_layout.addWidget(self.ip_temperature_display)
        ip_widget_layout.addWidget(ip_voltage_display_label)
        ip_widget_layout.addWidget(self.ip_voltage_display)
        ip_widget_layout.addWidget(ip_voltage_label)
        ip_widget_layout.addWidget(self.ip_voltage)
        ip_widget_layout.addWidget(self.ip_power)
        ip_widget_layout.addWidget(self.ip_lockswitch)
        ip_widget_layout.addWidget(self.ip_record)
        return QCustomGroupBox(ip_widget, "Ion Pump")

    def _makeNPwidget(self):
        np_widget = QWidget()
        np_widget_layout = QVBoxLayout(np_widget)
        # working time
        np_temperature_display_label = QLabel('Temperature (C)')
        self.np_temperature_display = QLabel('Temp')
        self.np_temperature_display.setFont(QFont(_SHELL_FONT, pointSize=20))
        self.np_temperature_display.setAlignment(Qt.AlignCenter)
        self.np_temperature_display.setStyleSheet('color: blue')
        # mode
        np_mode_label = QLabel('Mode')
        self.np_mode = QComboBox()
        self.np_mode.setFont(QFont(_SHELL_FONT, pointSize=12))
        self.np_mode.addItems(['Activation', 'Timed Activation', 'Conditioning', 'Timed Conditioning'])
        # power
        self.np_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.np_lockswitch.setChecked(True)
        self.np_power = TextChangingButton(('On', 'Off'))

        # lay out
        np_widget_layout.addWidget(np_temperature_display_label)
        np_widget_layout.addWidget(self.np_temperature_display)
        np_widget_layout.addWidget(np_mode_label)
        np_widget_layout.addWidget(self.np_mode)
        np_widget_layout.addWidget(self.np_power)
        np_widget_layout.addWidget(self.np_lockswitch)
        return QCustomGroupBox(np_widget, "Getter")

    def makeLayout(self):
        layout = QGridLayout(self)
        # menu
        self.header = QClientMenuHeader()
        layout.setMenuBar(self.header)
        # headers
        all_label = QLabel('NIOPS03 Pump')
        all_label.setFont(QFont(_SHELL_FONT, pointSize=20))
        all_label.setAlignment(Qt.AlignCenter)
        # create widgets
        ip_widget = self._makeIPwidget()
        np_widget = self._makeNPwidget()
        # lay out
        layout.addWidget(all_label,                         0, 0, 1, 2)
        layout.addWidget(ip_widget,                         1, 0, 12, 1)
        layout.addWidget(np_widget,                         1, 1, 11, 1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(niops03_gui)
