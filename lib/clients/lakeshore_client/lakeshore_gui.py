from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
import sys

from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class lakeshore_gui(QtWidgets.QFrame):
    def __init__(self, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout()
        self.setWindowTitle("Lakeshore 336 Temperature Controller")

    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        #temperature readout
        self.tempAll_label = QtWidgets.QLabel('Temperature Readout')
        self.tempAll_label.setFont(QFont(shell_font, pointSize= 20))
        self.tempAll_label.setAlignment(QtCore.Qt.AlignCenter)
            #diode 1
        self.temp1_label = QtWidgets.QLabel('Diode 1')
        self.temp1 = QtWidgets.QLabel('Diode 1')
        self.temp1.setFont(QFont(shell_font, pointSize=25))
        self.temp1.setAlignment(QtCore.Qt.AlignCenter)
        self.temp1.setStyleSheet('color: blue')
            #diode 2
        self.temp2_label = QtWidgets.QLabel('Diode 2')
        self.temp2 = QtWidgets.QLabel('Diode 2')
        self.temp2.setFont(QFont(shell_font, pointSize=25))
        self.temp2.setAlignment(QtCore.Qt.AlignCenter)
        self.temp2.setStyleSheet('color: blue')
            #diode 3
        self.temp3_label = QtWidgets.QLabel('Diode 3')
        self.temp3 = QtWidgets.QLabel('Diode 3')
        self.temp3.setFont(QFont(shell_font, pointSize=25))
        self.temp3.setAlignment(QtCore.Qt.AlignCenter)
        self.temp3.setStyleSheet('color: blue')
            #diode 4
        self.temp4_label = QtWidgets.QLabel('Diode 4')
        self.temp4 = QtWidgets.QLabel('Diode 4')
        self.temp4.setFont(QFont(shell_font, pointSize=25))
        self.temp4.setAlignment(QtCore.Qt.AlignCenter)
        self.temp4.setStyleSheet('color: blue')
            #record button
        self.record = TextChangingButton(('Start Recording', 'Stop Recording'))

        #heaters
        self.heatAll_label = QtWidgets.QLabel('Heater Configuration')
        self.heatAll_label.setFont(QFont(shell_font, pointSize= 20))
        self.heatAll_label.setAlignment(QtCore.Qt.AlignCenter)
        self.lockswitch = TextChangingButton(('Locked', 'Unlocked'))
            #heater 1
        self.heat1_label = QtWidgets.QLabel('Heater 1')
        self.heat1 = QtWidgets.QLabel('Current 1')
        self.heat1.setFont(QFont(shell_font, pointSize=25))
        self.heat1.setAlignment(QtCore.Qt.AlignCenter)
        self.heat1.setStyleSheet('color: red')
        self.heat1_toggle = TextChangingButton(('On', 'Off'))
        self.heat1_update = QtWidgets.QPushButton('Update')
                #mode function
        self.heat1_mode_label = QtWidgets.QLabel('Mode')
        self.heat1_mode = QtWidgets.QComboBox()
        self.heat1_mode.addItem('Off')
        self.heat1_mode.addItem('PID')
        self.heat1_mode.addItem('Zone')
        self.heat1_mode.addItem('Manual')
                #input control
        self.heat1_in_label = QtWidgets.QLabel('Input')
        self.heat1_in = QtWidgets.QComboBox()
        self.heat1_in.addItem('1')
        self.heat1_in.addItem('2')
        self.heat1_in.addItem('3')
        self.heat1_in.addItem('4')
                #resistance
        self.heat1_res_label = QtWidgets.QLabel('Resistance (Ohms)')
        self.heat1_res = QtWidgets.QComboBox()
        self.heat1_res.addItem('25')
        self.heat1_res.addItem('50')
                #max current
        self.heat1_curr_label = QtWidgets.QLabel('Max. Current (A)')
        self.heat1_curr = QtWidgets.QDoubleSpinBox()
        self.heat1_curr.setFont(QFont(shell_font, pointSize=16))
        self.heat1_curr.setDecimals(3)
        self.heat1_curr.setSingleStep(1e-3)
        self.heat1_curr.setRange(0, 2)
        self.heat1_curr.setKeyboardTracking(False)
                #setpoint
        self.heat1_set_label = QtWidgets.QLabel('Set Point (K)')
        self.heat1_set = QtWidgets.QDoubleSpinBox()
        self.heat1_set.setFont(QFont(shell_font, pointSize=16))
        self.heat1_set.setDecimals(3)
        self.heat1_set.setSingleStep(1e-3)
        self.heat1_set.setRange(0, 2)
        self.heat1_set.setKeyboardTracking(False)

        # highRail = QLabel('High Rail')
        # highRail.setFont(QFont(shell_font, pointSize=16))
        # highRail.setAlignment(QtCore.Qt.AlignCenter)
        # # dac voltage  label
        # setDacVoltage = QLabel(' Set Dac Voltage')
        # setDacVoltage.setFont(QFont(shell_font, pointSize=16))
        # setDacVoltage.setAlignment(QtCore.Qt.AlignCenter)
        # # clear lock button for voltage stuck too high
        # self.clear_lock = QPushButton('Clear Lock Voltage')
        # self.clear_lock.setMaximumHeight(30)
        # self.clear_lock.setFont(QFont('MS Shell Dlg 2', pointSize=12))

        layout.addWidget(self.tempAll_label, 1, 3)
        layout.addWidget(self.temp1, 3, 2, 3, 2)
        layout.addWidget(self.temp2, 8, 2, 3, 2)
        layout.addWidget(self.temp3, 13, 2, 3, 2)
        layout.addWidget(self.temp4, 18, 2, 3, 2)

        layout.addWidget(self.temp1_label, 2, 2)
        layout.addWidget(self.temp2_label, 7, 2)
        layout.addWidget(self.temp3_label, 12, 2)
        layout.addWidget(self.temp4_label, 17, 2)

        layout.addWidget(self.heatAll_label, 1, 15)
        layout.addWidget(self.heat1_label, 2, 7)
        layout.addWidget(self.heat1, 3, 10)
        layout.addWidget(self.heat1_mode_label, 5, 10)
        layout.addWidget(self.heat1_mode, 5, 7)
        # layout.addWidget(gainName, 2, 3, 1, 1)
        # layout.addWidget(self.spinGain, 3, 3, 1, 1)
        # layout.addWidget(lowRail, 4, 3, 1, 1)
        # layout.addWidget(self.spinLowRail, 5, 3, 1, 1)
        # layout.addWidget(highRail, 6, 3, 1, 1)
        # layout.addWidget(self.spinHighRail, 7, 3, 1, 1)
        # layout.addWidget(setDacVoltage, 8, 3, 1, 1)
        # layout.addWidget(self.spinDacVoltage, 9, 3, 1, 1)
        # layout.addWidget(self.dacLabel, 10, 3, 1, 1)
        # layout.addWidget(self.dacVoltage, 11, 3, 1, 1)

        layout.minimumSize()
        self.setLayout(layout)

    def lock(self):
        """
        fd
        """
        #todo: write


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = lakeshore_gui()
    icon.show()
    app.exec_()




