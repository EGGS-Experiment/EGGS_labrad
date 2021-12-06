from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
import sys

from EGGS_labrad.lib.clients.Widgets import TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class niops03_gui(QtWidgets.QFrame):
    def __init__(self, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("NIOPS03 Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(350, 325)
        self.all_label = QtWidgets.QLabel('NIOPS03 Pump')
        self.all_label.setFont(QFont(shell_font, pointSize=20))
        self.all_label.setAlignment(QtCore.Qt.AlignCenter)
        #niops03
        self.ip_label = QtWidgets.QLabel('Ion Pump')
        self.ip_label.setFont(QFont(shell_font, pointSize=15))
        self.ip_label.setAlignment(QtCore.Qt.AlignCenter)
            #pressure readout
        self.ip_pressure_display_label = QtWidgets.QLabel('Pressure (mbar)')
        self.ip_pressure_display = QtWidgets.QLabel('Pressure')
        self.ip_pressure_display.setFont(QFont(shell_font, pointSize=20))
        self.ip_pressure_display.setAlignment(QtCore.Qt.AlignCenter)
        self.ip_pressure_display.setStyleSheet('color: blue')
            #voltage setting
        self.ip_voltage_label = QtWidgets.QLabel('Voltage (V)')
        self.ip_voltage = QtWidgets.QDoubleSpinBox()
        self.ip_voltage.setFont(QFont(shell_font, pointSize=16))
        self.ip_voltage.setDecimals(0)
        self.ip_voltage.setSingleStep(1)
        self.ip_voltage.setRange(0, 6000)
        self.ip_voltage.setKeyboardTracking(False)
            #working time
        self.ip_workingtime_display_label = QtWidgets.QLabel('Working Time (Hours:Minutes)')
        self.ip_workingtime_display = QtWidgets.QLabel('00:00')
        self.ip_workingtime_display.setFont(QFont(shell_font, pointSize=20))
        self.ip_workingtime_display.setAlignment(QtCore.Qt.AlignCenter)
        self.ip_workingtime_display.setStyleSheet('color: blue')
            #record button
        self.ip_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #power
        self.ip_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.ip_lockswitch.setChecked(True)
        self.ip_power = TextChangingButton(('On', 'Off'))

        #getter
        self.np_label = QtWidgets.QLabel('Getter')
        self.np_label.setFont(QFont(shell_font, pointSize=15))
        self.np_label.setAlignment(QtCore.Qt.AlignCenter)
            #working time
        self.np_workingtime_display_label = QtWidgets.QLabel('Working Time (Hours:Minutes)')
        self.np_workingtime_display = QtWidgets.QLabel('00:00')
        self.np_workingtime_display.setFont(QFont(shell_font, pointSize=20))
        self.np_workingtime_display.setAlignment(QtCore.Qt.AlignCenter)
        self.np_workingtime_display.setStyleSheet('color: blue')
            #mode
        self.np_mode_label = QtWidgets.QLabel('Mode')
        self.np_mode = QtWidgets.QComboBox()
        self.np_mode.setFont(QFont(shell_font, pointSize=12))
        self.np_mode.addItems(['Activation', 'Timed Activation', 'Conditioning', 'Timed Conditioning'])
            #power
        self.np_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.np_lockswitch.setChecked(True)
        self.np_power = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        layout.addWidget(self.all_label, 0, 0, 1, 2)

        pump1_col = 0
        pump2_col = 1

        layout.addWidget(self.ip_label, 1, pump1_col)
        layout.addWidget(self.ip_pressure_display_label, 2, pump1_col)
        layout.addWidget(self.ip_pressure_display, 3, pump1_col)
        layout.addWidget(self.ip_workingtime_display_label, 4, pump1_col)
        layout.addWidget(self.ip_workingtime_display, 5, pump1_col)
        layout.addWidget(self.ip_voltage_label, 6, pump1_col)
        layout.addWidget(self.ip_voltage, 7, pump1_col)
        layout.addWidget(self.ip_power, 8, pump1_col)
        layout.addWidget(self.ip_lockswitch, 9, pump1_col)
        layout.addWidget(self.ip_record, 10, pump1_col)

        layout.addWidget(self.np_label, 1, pump2_col)
        layout.addWidget(self.np_workingtime_display_label, 4, pump2_col)
        layout.addWidget(self.np_workingtime_display, 5, pump2_col)
        layout.addWidget(self.np_mode_label, 6, pump2_col)
        layout.addWidget(self.np_mode, 7, pump2_col)
        layout.addWidget(self.np_power, 8, pump2_col)
        layout.addWidget(self.np_lockswitch, 9, pump2_col)

        #layout.minimumSize()
        self.setLayout(layout)


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(niops03_gui)




