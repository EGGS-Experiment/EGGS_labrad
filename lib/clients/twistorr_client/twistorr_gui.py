from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
import sys

from EGGS_labrad.lib.clients.Widgets.q_custom_text_changing_button import TextChangingButton as _TextChangingButton

class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)

class twistorr_gui(QtWidgets.QFrame):
    def __init__(self, parent=None):
        window = QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Twistorr 74 Pump Controller")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'

        #pressure readout
        self.press_label = QtWidgets.QLabel('Pressure (mbar)')
        self.press_display = QtWidgets.QLabel('Pressure')
        self.press_display.setFont(QFont(shell_font, pointSize=25))
        self.press_display.setAlignment(QtCore.Qt.AlignCenter)
        self.press_display.setStyleSheet('color: blue')

        #record button
        self.press_record = TextChangingButton(('Stop Recording', 'Start Recording'))

        #power
        self.toggle_lockswitch = TextChangingButton(('Lock', 'Unlock'))
        self.power_button = TextChangingButton(('On', 'Off'))


    def makeLayout(self):
        layout = QtWidgets.QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        layout.addWidget(self.press_label, 1, 1)
        layout.addWidget(self.press_display, 2, 1, 3, 5)
        layout.addWidget(self.power_button, 6, 1, 1, 5)
        layout.addWidget(self.toggle_lockswitch, 7, 1, 1, 5)
        layout.addWidget(self.press_record, 8, 1, 1, 5)

        layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon = twistorr_gui()
    icon.show()
    app.exec_()




