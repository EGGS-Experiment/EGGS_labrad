from PyQt5 import QtCore, QtGui, QtWidgets
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
            #diode 1
        self.temp1_label = QtWidgets.QLabel('Diode 1')
        self.temp1 = QtWidgets.QLabel('Diode 1')
        self.temp1.setFont(QtGui.QFont(shell_font, pointSize=25))
        self.temp1.setAlignment(QtCore.Qt.AlignCenter)
        self.temp1.setStyleSheet('color: blue')
            #diode 2
        self.temp2_label = QtWidgets.QLabel('Diode 2')
        self.temp2 = QtWidgets.QLabel('Diode 2')
        self.temp2.setFont(QtGui.QFont(shell_font, pointSize=25))
        self.temp2.setAlignment(QtCore.Qt.AlignCenter)
        self.temp2.setStyleSheet('color: blue')
            #diode 3
        self.temp3_label = QtWidgets.QLabel('Diode 3')
        self.temp3 = QtWidgets.QLabel('Diode 3')
        self.temp3.setFont(QtGui.QFont(shell_font, pointSize=25))
        self.temp3.setAlignment(QtCore.Qt.AlignCenter)
        self.temp3.setStyleSheet('color: blue')
            #diode 4
        self.temp4_label = QtWidgets.QLabel('Diode 4')
        self.temp4 = QtWidgets.QLabel('Diode 4')
        self.temp4.setFont(QtGui.QFont(shell_font, pointSize=25))
        self.temp4.setAlignment(QtCore.Qt.AlignCenter)
        self.temp4.setStyleSheet('color: blue')
            #record button
        self.record = TextChangingButton(('Start Recording', 'Stop Recording'))

        #heaters
        self.heatAll_label = QtWidgets.QLabel('Heater Configuration')
        self.lockswitch = TextChangingButton(('Locked', 'Unlocked'))
            #heater 1
        self.heat1_label = QtWidgets.QLabel('Heater 1')
        self.heat1 = QtWidgets.QLabel('Current 1')
        self.heat1.setFont(QtGui.QFont(shell_font, pointSize=25))
        self.heat1.setAlignment(QtCore.Qt.AlignCenter)
        self.heat1.setStyleSheet('color: red')
        self.heat1_toggle = TextChangingButton(('On', 'Off'))
        self.heat1_update = QtWidgets.QPushButton('Update')
                #mode function
        self.heat1_mode = QtWidgets.QComboBox()
        self.heat1_mode.addItem('Off')
        self.heat1_mode.addItem('PID')
        self.heat1_mode.addItem('Zone')
        self.heat1_mode.addItem('Manual')
                #input control
        self.heat1_in = QtWidgets.QComboBox()
        self.heat1_in.addItem('1')
        self.heat1_in.addItem('2')
        self.heat1_in.addItem('3')
        self.heat1_in.addItem('4')
                #resistance
        self.heat1_res = QtWidgets.QComboBox()
        self.heat1_res.addItem('25')
        self.heat1_res.addItem('50')
                #max current
        self.spinGain = QDoubleSpinBox()
        self.spinGain.setFont(QFont(shell_font, pointSize=16))
        self.spinGain.setDecimals(3)
        self.spinGain.setSingleStep(1e-3)
        self.spinGain.setRange(0, 2)
        self.spinGain.setKeyboardTracking(False)

        # # gain  label
        # gainName = QLabel('Gain')
        # gainName.setFont(QFont(shell_font, pointSize=16))
        # gainName.setAlignment(QtCore.Qt.AlignCenter)
        # # rails  label
        # lowRail = QLabel('Low Rail')
        # lowRail.setFont(QFont(shell_font, pointSize=16))
        # lowRail.setAlignment(QtCore.Qt.AlignCenter)
        # # high rails  label
        # highRail = QLabel('High Rail')
        # highRail.setFont(QFont(shell_font, pointSize=16))
        # highRail.setAlignment(QtCore.Qt.AlignCenter)
        # # dac voltage  label
        # setDacVoltage = QLabel(' Set Dac Voltage')
        # setDacVoltage.setFont(QtGui.QFont(shell_font, pointSize=16))
        # setDacVoltage.setAlignment(QtCore.Qt.AlignCenter)
        # # clear lock button for voltage stuck too high
        # self.clear_lock = QPushButton('Clear Lock Voltage')
        # self.clear_lock.setMaximumHeight(30)
        # self.clear_lock.setFont(QFont('MS Shell Dlg 2', pointSize=12))

        layout.addWidget(self.tempAll_label, 1, 3)
        layout.addWidget(self.temp1, 2, 2, 3, 2)
        layout.addWidget(self.temp2, 7, 2, 3, 2)
        layout.addWidget(self.temp3, 12, 2, 3, 2)
        layout.addWidget(self.temp4, 17, 2, 3, 2)

        layout.addWidget(self.temp1_label, 1, 2)
        layout.addWidget(self.temp2_label, 6, 2)
        layout.addWidget(self.temp3_label, 11, 2)
        layout.addWidget(self.temp4_label, 16, 2)

        layout.addWidget(self.lockswitch, 1, 3, 1, 1)
        layout.addWidget(self.heat)
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = lakeshore_gui('Lakeshore 336 Temperature Controller')
    icon.show()
    app.exec_()




