from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
import sys

from EGGS_labrad.lib.clients.Widgets import TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class lakeshore336_gui(QtWidgets.QFrame):
    def __init__(self, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Lakeshore 336 Temperature Controller")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.lakeshore_label = QtWidgets.QLabel('Lakeshore 336 Controller')
        self.lakeshore_label.setFont(QFont(shell_font, pointSize=20))
        self.lakeshore_label.setAlignment(QtCore.Qt.AlignCenter)
        #temperature readout
        self.tempAll_label = QtWidgets.QLabel('Temperature Readout')
        self.tempAll_label.setFont(QFont(shell_font, pointSize= 15))
        self.tempAll_label.setAlignment(QtCore.Qt.AlignCenter)
            #record button
        self.tempAll_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #diode 1
        self.temp1_label = QtWidgets.QLabel('Diode 1 (K)')
        self.temp1 = QtWidgets.QLabel('Diode 1')
        self.temp1.setFont(QFont(shell_font, pointSize=25))
        self.temp1.setAlignment(QtCore.Qt.AlignCenter)
        self.temp1.setStyleSheet('color: blue')
            #diode 2
        self.temp2_label = QtWidgets.QLabel('Diode 2 (K)')
        self.temp2 = QtWidgets.QLabel('Diode 2')
        self.temp2.setFont(QFont(shell_font, pointSize=25))
        self.temp2.setAlignment(QtCore.Qt.AlignCenter)
        self.temp2.setStyleSheet('color: blue')
            #diode 3
        self.temp3_label = QtWidgets.QLabel('Diode 3 (K)')
        self.temp3 = QtWidgets.QLabel('Diode 3')
        self.temp3.setFont(QFont(shell_font, pointSize=25))
        self.temp3.setAlignment(QtCore.Qt.AlignCenter)
        self.temp3.setStyleSheet('color: blue')
            #diode 4
        self.temp4_label = QtWidgets.QLabel('Diode 4 (K)')
        self.temp4 = QtWidgets.QLabel('Diode 4')
        self.temp4.setFont(QFont(shell_font, pointSize=25))
        self.temp4.setAlignment(QtCore.Qt.AlignCenter)
        self.temp4.setStyleSheet('color: blue')

        #heaters
        self.heatAll_label = QtWidgets.QLabel('Heater Configuration')
        self.heatAll_label.setFont(QFont(shell_font, pointSize= 15))
        self.heatAll_label.setAlignment(QtCore.Qt.AlignCenter)
        self.heatAll_lockswitch = TextChangingButton(('Lock', 'Unlock'))
            #heater output
        self.heat1_label = QtWidgets.QLabel('Heater 1')
        self.heat1 = QtWidgets.QLabel('Current 1')
        self.heat1.setFont(QFont(shell_font, pointSize=25))
        self.heat1.setAlignment(QtCore.Qt.AlignCenter)
        self.heat1.setStyleSheet('color: red')
        self.heat1_update = QtWidgets.QPushButton('Update')

        self.heat2_label = QtWidgets.QLabel('Heater 2')
        self.heat2 = QtWidgets.QLabel('Current 2')
        self.heat2.setFont(QFont(shell_font, pointSize=25))
        self.heat2.setAlignment(QtCore.Qt.AlignCenter)
        self.heat2.setStyleSheet('color: red')
        self.heat2_update = QtWidgets.QPushButton('Update')
            #mode function
        self.heat1_mode_label = QtWidgets.QLabel('Mode')
        self.heat1_mode = QtWidgets.QComboBox()
        self.heat1_mode.addItem('Off')
        self.heat1_mode.addItem('Autotune')
        self.heat1_mode.addItem('PID')
        self.heat1_mode.addItem('Manual')
        #self.heat1_mode.addItem('Zone')

        self.heat2_mode_label = QtWidgets.QLabel('Mode')
        self.heat2_mode = QtWidgets.QComboBox()
        self.heat2_mode.addItem('Off')
        self.heat2_mode.addItem('Autotune')
        self.heat2_mode.addItem('PID')
        self.heat2_mode.addItem('Manual')
        #self.heat2_mode.addItem('Zone')
                #input control
        self.heat1_in_label = QtWidgets.QLabel('Input')
        self.heat1_in = QtWidgets.QComboBox()
        self.heat1_in.addItem('1')
        self.heat1_in.addItem('2')
        self.heat1_in.addItem('3')
        self.heat1_in.addItem('4')

        self.heat2_in_label = QtWidgets.QLabel('Input')
        self.heat2_in = QtWidgets.QComboBox()
        self.heat2_in.addItem('1')
        self.heat2_in.addItem('2')
        self.heat2_in.addItem('3')
        self.heat2_in.addItem('4')
                #resistance
        self.heat1_res_label = QtWidgets.QLabel('Resistance (Ohms)')
        self.heat1_res = QtWidgets.QComboBox()
        self.heat1_res.addItem('25')
        self.heat1_res.addItem('50')

        self.heat2_res_label = QtWidgets.QLabel('Resistance (Ohms)')
        self.heat2_res = QtWidgets.QComboBox()
        self.heat2_res.addItem('25')
        self.heat2_res.addItem('50')
                #max current
        self.heat1_curr_label = QtWidgets.QLabel('Max. Current (A)')
        self.heat1_curr = QtWidgets.QDoubleSpinBox()
        self.heat1_curr.setFont(QFont(shell_font, pointSize=16))
        self.heat1_curr.setDecimals(3)
        self.heat1_curr.setSingleStep(1e-3)
        self.heat1_curr.setRange(0, 2)
        self.heat1_curr.setKeyboardTracking(False)

        self.heat2_curr_label = QtWidgets.QLabel('Max. Current (A)')
        self.heat2_curr = QtWidgets.QDoubleSpinBox()
        self.heat2_curr.setFont(QFont(shell_font, pointSize=16))
        self.heat2_curr.setDecimals(3)
        self.heat2_curr.setSingleStep(1e-3)
        self.heat2_curr.setRange(0, 2)
        self.heat2_curr.setKeyboardTracking(False)
                #setpoint
        self.heat1_set_label = QtWidgets.QLabel('Set Point (K)')
        self.heat1_set = QtWidgets.QDoubleSpinBox()
        self.heat1_set.setFont(QFont(shell_font, pointSize=16))
        self.heat1_set.setDecimals(3)
        self.heat1_set.setSingleStep(1e-3)
        self.heat1_set.setRange(0, 2)
        self.heat1_set.setKeyboardTracking(False)

        self.heat2_set_label = QtWidgets.QLabel('Set Point (K)')
        self.heat2_set = QtWidgets.QDoubleSpinBox()
        self.heat2_set.setFont(QFont(shell_font, pointSize=16))
        self.heat2_set.setDecimals(3)
        self.heat2_set.setSingleStep(1e-3)
        self.heat2_set.setRange(0, 2)
        self.heat2_set.setKeyboardTracking(False)
            #range function
        self.heat1_range_label = QtWidgets.QLabel('Range')
        self.heat1_range = QtWidgets.QComboBox()
        self.heat1_range.addItem('0')
        self.heat1_range.addItem('1')
        self.heat1_range.addItem('2')
        self.heat1_range.addItem('3')

        self.heat2_range_label = QtWidgets.QLabel('Range')
        self.heat2_range = QtWidgets.QComboBox()
        self.heat2_range.addItem('0')
        self.heat2_range.addItem('1')
        self.heat2_range.addItem('2')
        self.heat2_range.addItem('3')
                #control 1
        self.heat1_p1_label = QtWidgets.QLabel('Parameter 1')
        self.heat1_p1 = QtWidgets.QDoubleSpinBox()
        self.heat1_p1.setFont(QFont(shell_font, pointSize=16))
        self.heat1_p1.setDecimals(3)
        self.heat1_p1.setSingleStep(1e-3)
        #self.heat1_p1.setRange(0, 2)
        self.heat1_p1.setKeyboardTracking(False)

        self.heat2_p1_label = QtWidgets.QLabel('Parameter 1')
        self.heat2_p1 = QtWidgets.QDoubleSpinBox()
        self.heat2_p1.setFont(QFont(shell_font, pointSize=16))
        self.heat2_p1.setDecimals(3)
        self.heat2_p1.setSingleStep(1e-3)
        #self.heat2_p1.setRange(0, 1000)
        self.heat2_p1.setKeyboardTracking(False)
                #control 2
        self.heat1_p2_label = QtWidgets.QLabel('Parameter 2')
        self.heat1_p2 = QtWidgets.QDoubleSpinBox()
        self.heat1_p2.setFont(QFont(shell_font, pointSize=16))
        self.heat1_p2.setDecimals(1)
        self.heat1_p2.setSingleStep(1e-1)
        self.heat1_p2.setRange(0, 1000)
        self.heat1_p2.setKeyboardTracking(False)

        self.heat2_p2_label = QtWidgets.QLabel('Parameter 2')
        self.heat2_p2 = QtWidgets.QDoubleSpinBox()
        self.heat2_p2.setFont(QFont(shell_font, pointSize=16))
        self.heat2_p2.setDecimals(3)
        self.heat2_p2.setSingleStep(1e-3)
        #self.heat2_p2.setRange(0, 2)
        self.heat2_p2.setKeyboardTracking(False)
                #control 3
        self.heat1_p3_label = QtWidgets.QLabel('Parameter 3')
        self.heat1_p3 = QtWidgets.QDoubleSpinBox()
        self.heat1_p3.setFont(QFont(shell_font, pointSize=16))
        self.heat1_p3.setDecimals(0)
        self.heat1_p3.setSingleStep(1)
        self.heat1_p3.setRange(0, 200)
        self.heat1_p3.setKeyboardTracking(False)

        self.heat2_p3_label = QtWidgets.QLabel('Parameter 3')
        self.heat2_p3 = QtWidgets.QDoubleSpinBox()
        self.heat2_p3.setFont(QFont(shell_font, pointSize=16))
        self.heat2_p3.setDecimals(0)
        self.heat2_p3.setSingleStep(1)
        self.heat2_p3.setRange(0, 200)
        self.heat2_p3.setKeyboardTracking(False)

    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        temp_layout = QtWidgets.QVBoxLayout()
        heat1_layout = QtWidgets.QVBoxLayout()
        heat2_layout = QtWidgets.QVBoxLayout()

        temp_label_col = 2
        temp_box_col = 2

        heatAll_col = 11

        heat1_label_col = 9
        heat1_box_col = 11

        heat2_label_col = 13
        heat2_box_col = 15

        heat_box_start = 6
        heat_box_step = 1

        layout.addWidget(self.lakeshore_label, 0, 0, 1, 16)
        layout.addWidget(self.tempAll_label, 1, 2)
        layout.addWidget(self.tempAll_record, 2, 2)

        layout.addWidget(self.temp1, 4, temp_box_col, 3, 2)
        layout.addWidget(self.temp2, 6, temp_box_col, 3, 2)
        layout.addWidget(self.temp3, 8, temp_box_col, 3, 2)
        layout.addWidget(self.temp4, 10, temp_box_col, 3, 2)

        layout.addWidget(self.temp1_label, 4, temp_label_col)
        layout.addWidget(self.temp2_label, 6, temp_label_col)
        layout.addWidget(self.temp3_label, 8, temp_label_col)
        layout.addWidget(self.temp4_label, 10, temp_label_col)

        layout.addWidget(self.heatAll_label, 1, heatAll_col, 1, 5)
        layout.addWidget(self.heatAll_lockswitch, 2, heatAll_col + 1, 1, 2)

        layout.addWidget(self.heat1_label, 3, heat1_box_col)
        layout.addWidget(self.heat1, 4, heat1_box_col)
        layout.addWidget(self.heat1_mode_label, heat_box_start, heat1_label_col)
        layout.addWidget(self.heat1_mode, heat_box_start, heat1_box_col)
        layout.addWidget(self.heat1_in_label, heat_box_start + 1 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_in, heat_box_start + 1 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_res_label, heat_box_start + 2 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_res, heat_box_start + 2 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_curr_label, heat_box_start + 3 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_curr, heat_box_start + 3 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_range_label, heat_box_start + 4 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_range, heat_box_start + 4 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_set_label, heat_box_start + 5 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_set, heat_box_start + 5 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_p1_label, heat_box_start + 6 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_p1, heat_box_start + 6 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_p2_label, heat_box_start + 7 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_p2, heat_box_start + 7 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_p3_label, heat_box_start + 8 * heat_box_step, heat1_label_col)
        layout.addWidget(self.heat1_p3, heat_box_start + 8 * heat_box_step, heat1_box_col)
        layout.addWidget(self.heat1_update, heat_box_start + 9 * heat_box_step, heat1_box_col)

        layout.addWidget(self.heat2_label, 3, heat2_box_col)
        layout.addWidget(self.heat2, 4, heat2_box_col)
        layout.addWidget(self.heat2_mode_label, heat_box_start, heat2_label_col)
        layout.addWidget(self.heat2_mode, heat_box_start, heat2_box_col)
        layout.addWidget(self.heat2_in_label, heat_box_start + 1 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_in, heat_box_start + 1 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_res_label, heat_box_start + 2 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_res, heat_box_start + 2 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_curr_label, heat_box_start + 3 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_curr, heat_box_start + 3 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_range_label, heat_box_start + 4 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_range, heat_box_start + 4 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_set_label, heat_box_start + 5 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_set, heat_box_start + 5 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_p1_label, heat_box_start + 6 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_p1, heat_box_start + 6 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_p2_label, heat_box_start + 7 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_p2, heat_box_start + 7 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_p3_label, heat_box_start + 8 * heat_box_step, heat2_label_col)
        layout.addWidget(self.heat2_p3, heat_box_start + 8 * heat_box_step, heat2_box_col)
        layout.addWidget(self.heat2_update, heat_box_start + 9 * heat_box_step, heat2_box_col)

        layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(lakeshore336_gui)



