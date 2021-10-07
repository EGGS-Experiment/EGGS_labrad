from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from common.lib.clients.qtui.q_custom_text_changing_button import \
    TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class lakeshore_gui(QtWidgets.QFrame):
    def __init__(self, chanName, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(chanName)
        self.setWindowTitle(chanName)

    def makeLayout(self, name):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        #temperature readout
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
        self.lockswitch = TextChangingButton(('Locked', 'Unlocked'))
            #heater 1
        self.heat1_toggle = TextChangingButton(('On', 'Off'))
        self.heat1_update = QtWidgets.QPushButton('Update')



        # # gain  label
        # gainName = QLabel('Gain')
        # gainName.setFont(QFont(shell_font, pointSize=16))
        # gainName.setAlignment(QtCore.Qt.AlignCenter)
        #
        # # gain
        # self.spinGain = QDoubleSpinBox()
        # self.spinGain.setFont(QFont(shell_font, pointSize=16))
        # self.spinGain.setDecimals(6)
        # self.spinGain.setSingleStep(1e-6)
        # self.spinGain.setRange(1e-6, 1)
        # self.spinGain.setKeyboardTracking(False)
        #
        # # rails  label
        # lowRail = QLabel('Low Rail')
        # lowRail.setFont(QFont(shell_font, pointSize=16))
        # lowRail.setAlignment(QtCore.Qt.AlignCenter)
        #
        # # low rail
        # self.spinLowRail = QDoubleSpinBox()
        # self.spinLowRail.setFont(QFont(shell_font, pointSize=16))
        # self.spinLowRail.setDecimals(3)
        # self.spinLowRail.setSingleStep(.001)
        # self.spinLowRail.setRange(0, 100)
        # self.spinLowRail.setKeyboardTracking(False)
        #
        # # high rails  label
        # highRail = QLabel('High Rail')
        # highRail.setFont(QFont(shell_font, pointSize=16))
        # highRail.setAlignment(QtCore.Qt.AlignCenter)
        #
        # # high rail
        # self.spinHighRail = QDoubleSpinBox()
        # self.spinHighRail.setFont(QFont(shell_font, pointSize=16))
        # self.spinHighRail.setDecimals(3)
        # self.spinHighRail.setSingleStep(.001)
        # self.spinHighRail.setRange(0, 100)
        # self.spinHighRail.setKeyboardTracking(False)
        #
        # # dac voltage  label
        # setDacVoltage = QLabel(' Set Dac Voltage')
        # setDacVoltage.setFont(QtGui.QFont(shell_font, pointSize=16))
        # setDacVoltage.setAlignment(QtCore.Qt.AlignCenter)
        #
        # # set dac voltage
        # self.spinDacVoltage = QDoubleSpinBox()
        # self.spinDacVoltage.setFont(QFont(shell_font, pointSize=16))
        # self.spinDacVoltage.setDecimals(3)
        # self.spinDacVoltage.setSingleStep(.001)
        # self.spinDacVoltage.setRange(0, 100)
        # self.spinDacVoltage.setKeyboardTracking(False)
        #
        # # clear lock button for voltage stuck too high
        # self.clear_lock = QPushButton('Clear Lock Voltage')
        # self.clear_lock.setMaximumHeight(30)
        # self.clear_lock.setFont(QFont('MS Shell Dlg 2', pointSize=12))

        layout.addWidget(self.temp1, 2, 2, 3, 2)
        layout.addWidget(self.temp2, 7, 2, 3, 2)
        layout.addWidget(self.temp3, 12, 2, 3, 2)
        layout.addWidget(self.temp4, 17, 2, 3, 2)

        layout.addWidget(self.temp1_label, 1, 2)
        layout.addWidget(self.temp2_label, 6, 2)
        layout.addWidget(self.temp3_label, 11, 2)
        layout.addWidget(self.temp4_label, 16, 2)


        layout.addWidget(self.lockswitch, 1, 3, 1, 1)
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




