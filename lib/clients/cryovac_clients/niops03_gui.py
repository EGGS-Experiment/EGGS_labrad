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
        self.niops_label = QtWidgets.QLabel('Ion Pump')
        self.niops_label.setFont(QFont(shell_font, pointSize=15))
        self.niops_label.setAlignment(QtCore.Qt.AlignCenter)
            #pressure readout
        self.niops_pressure_display_label = QtWidgets.QLabel('Pressure (mbar)')
        self.niops_pressure_display = QtWidgets.QLabel('Pressure')
        self.niops_pressure_display.setFont(QFont(shell_font, pointSize=20))
        self.niops_pressure_display.setAlignment(QtCore.Qt.AlignCenter)
        self.niops_pressure_display.setStyleSheet('color: blue')
            #voltage setting
        self.niops_voltage_label = QtWidgets.QLabel('Voltage (V)')
        self.niops_voltage = QtWidgets.QDoubleSpinBox()
        self.niops_voltage.setFont(QFont(shell_font, pointSize=16))
        self.niops_voltage.setDecimals(0)
        self.niops_voltage.setSingleStep(1)
        self.niops_voltage.setRange(0, 6000)
        self.niops_voltage.setKeyboardTracking(False)
            #working time
        self.niops_workingtime_display_label = QtWidgets.QLabel('Working Time (Hours:Minutes)')
        self.niops_workingtime_display = QtWidgets.QLabel('00:00')
        self.niops_workingtime_display.setFont(QFont(shell_font, pointSize=20))
        self.niops_workingtime_display.setAlignment(QtCore.Qt.AlignCenter)
        self.niops_workingtime_display.setStyleSheet('color: blue')
            #record button
        self.niops_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #power
        self.niops_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.niops_lockswitch.setChecked(True)
        self.niops_power = TextChangingButton(('On', 'Off'))

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

        layout.addWidget(self.niops_label, 1, pump1_col)
        layout.addWidget(self.niops_pressure_display_label, 2, pump1_col)
        layout.addWidget(self.niops_pressure_display, 3, pump1_col)
        layout.addWidget(self.niops_workingtime_display_label, 4, pump1_col)
        layout.addWidget(self.niops_workingtime_display, 5, pump1_col)
        layout.addWidget(self.niops_voltage_label, 6, pump1_col)
        layout.addWidget(self.niops_voltage, 7, pump1_col)
        layout.addWidget(self.niops_power, 8, pump1_col)
        layout.addWidget(self.niops_lockswitch, 9, pump1_col)
        layout.addWidget(self.niops_record, 10, pump1_col)

        layout.addWidget(self.np_label, 1, pump2_col)
        layout.addWidget(self.np_workingtime_display_label, 4, pump2_col)
        layout.addWidget(self.np_workingtime_display, 5, pump2_col)
        layout.addWidget(self.np_power, 8, pump2_col)
        layout.addWidget(self.np_lockswitch, 9, pump2_col)

        #layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(niops03_gui)




