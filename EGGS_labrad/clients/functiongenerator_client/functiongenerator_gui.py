from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, QClientMenuHeader


class functiongenerator_gui(QFrame):
    """
    GUI for a function generator.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(name)
        self.setMinimumSize(300, 125)
        self.setMaximumSize(350, 150)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        title.setAlignment(Qt.AlignCenter)
        freqlabel = QLabel('Frequency (kHz)')
        powerlabel = QLabel('Amplitude (V)')
        attlabel = QLabel('Attenuation (dBm)')
        # editable fields
        self.freq = QDoubleSpinBox()
        self.freq.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.freq.setDecimals(2)
        self.freq.setSingleStep(0.01)
        self.freq.setRange(1, 1e4) # in kHz
        self.freq.setKeyboardTracking(False)
        self.ampl = QDoubleSpinBox()
        self.ampl.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.ampl.setDecimals(2)
        self.ampl.setSingleStep(0.01)
        self.ampl.setRange(0.01, 1e1)
        self.ampl.setKeyboardTracking(False)
        # self.att = QDoubleSpinBox()
        # self.att.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        # self.att.setDecimals(3)
        # self.att.setSingleStep(0.1)
        # self.att.setRange(-145.0, 30.0)
        #self.att.setKeyboardTracking(False)
        self.resetswitch = QPushButton('Initialize')
        self.rfswitch = TextChangingButton(("On", "Off"))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))
        # create header
        #self.header = QClientMenuHeader()
        # add widgets to layout
        #layout.setMenuBar(self.header)
        layout.addWidget(title,             1, 0, 1, 3)
        layout.addWidget(freqlabel,         2, 0, 1, 1)
        layout.addWidget(powerlabel,        2, 1, 1, 1)
        #layout.addWidget(attlabel,         2, 2, 1, 1)
        layout.addWidget(self.freq,         3, 0)
        layout.addWidget(self.ampl,         3, 1)
        #layout.addWidget(self.att,         3, 2)
        layout.addWidget(self.resetswitch,  4, 0)
        layout.addWidget(self.rfswitch,     4, 1)
        layout.addWidget(self.lockswitch,   4, 2)

    def lock(self, status):
        self.freq.setEnabled(status)
        self.ampl.setEnabled(status)
        #self.att.setEnabled(status)
        self.rfswitch.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(functiongenerator_gui)
