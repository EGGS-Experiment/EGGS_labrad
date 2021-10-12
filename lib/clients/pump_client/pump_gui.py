from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
import sys

from EGGS_labrad.lib.clients.Widgets.q_custom_text_changing_button import TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class pump_gui(QtWidgets.QFrame):
    def __init__(self, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Pump Clients")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'

        #twistorr 74
        self.twistorr_label = QtWidgets.QLabel('Twistorr 74 Pump')
        self.twistorr_label.setFont(QFont(shell_font, pointSize= 20))
        self.twistorr_label.setAlignment(QtCore.Qt.AlignCenter)
            #readout
        self.twistorr_display_label = QtWidgets.QLabel('Pressure (mbar)')
        self.twistorr_display = QtWidgets.QLabel('Pressure')
        self.twistorr_display.setFont(QFont(shell_font, pointSize=25))
        self.twistorr_display.setAlignment(QtCore.Qt.AlignCenter)
        self.twistorr_display.setStyleSheet('color: blue')
            #record button
        self.twistorr_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #power
        self.twistorr_lockswitch = TextChangingButton(('Lock', 'Unlock'))
        self.twistorr_power = TextChangingButton(('On', 'Off'))

        #niops03
        self.niops_label = QtWidgets.QLabel('NIOPS 03 Pump')
        self.niops_label.setFont(QFont(shell_font, pointSize= 20))
        self.niops_label.setAlignment(QtCore.Qt.AlignCenter)
            #power
        self.niops_lockswitch = TextChangingButton(('Lock', 'Unlock'))
        self.niops_power = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        pump1_col = 1
        pump2_col = 7

        layout.addWidget(self.twistorr_label, 1, pump1_col)
        layout.addWidget(self.twistorr_display_label, 2, pump1_col)
        layout.addWidget(self.twistorr_display, 3, pump1_col, 3, 5)
        layout.addWidget(self.twistorr_power, 7, pump1_col, 1, 5)
        layout.addWidget(self.twistorr_lockswitch, 8, pump1_col, 1, 5)
        layout.addWidget(self.twistorr_record, 9, pump1_col, 1, 5)

        layout.addWidget(self.niops_label, 1, pump2_col)
        layout.addWidget(self.niops_power, 3, pump2_col)
        layout.addWidget(self.niops_lockswitch, 4, pump2_col)

        layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = pump_gui()
    icon.show()
    app.exec_()




