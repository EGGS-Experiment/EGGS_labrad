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

        #niops03
        self.niops_label = QtWidgets.QLabel('NIOPS 03 Pump')
        self.niops_label.setFont(QFont(shell_font, pointSize= 20))
        self.niops_label.setAlignment(QtCore.Qt.AlignCenter)
            #readout
        self.niops_display_label = QtWidgets.QLabel('Pressure (mbar)')
        self.niops_display = QtWidgets.QLabel('Pressure')
        self.niops_display.setFont(QFont(shell_font, pointSize=25))
        self.niops_display.setAlignment(QtCore.Qt.AlignCenter)
        self.niops_display.setStyleSheet('color: blue')
            #record button
        self.niops_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #power
        self.niops_lockswitch = TextChangingButton(('Lock', 'Unlock'))
        self.niops_power = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        pump1_col = 1
        pump2_col = 9

        layout.addWidget(self.niops_label, 1, pump1_col)
        layout.addWidget(self.niops_display_label, 2, pump1_col)
        layout.addWidget(self.niops_display, 3, pump1_col, 3, 5)
        layout.addWidget(self.niops_power, 7, pump1_col, 1, 5)
        layout.addWidget(self.niops_lockswitch, 8, pump1_col, 1, 5)
        layout.addWidget(self.niops_record, 9, pump1_col, 1, 5)

        layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = niops03_gui()
    icon.show()
    app.exec_()




