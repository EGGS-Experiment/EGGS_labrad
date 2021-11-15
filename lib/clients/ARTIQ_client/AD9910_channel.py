import sys
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QApplication, QDoubleSpinBox, QLabel, QGridLayout, QFrame
from EGGS_labrad.lib.clients.Widgets import TextChangingButton

class AD9910_channel_GUI(QFrame):
    def __init__(self, title=None, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title)

    def makeLayout(self, title):
        layout = QGridLayout()
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        freqlabel = QLabel('Frequency (MHz)')
        powerlabel = QLabel('Amplitude (V)')
        attlabel = QLabel('Attenuation (dBm)')
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(freqlabel, 1, 0, 1, 1)
        layout.addWidget(powerlabel, 1, 1, 1, 1)
        layout.addWidget(attlabel, 3, 0, 1, 1)

        # editable fields
        self.freq = QDoubleSpinBox()
        self.freq.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.freq.setDecimals(3)
        self.freq.setSingleStep(0.1)
        self.freq.setRange(10.0, 250.0)
        self.freq.setKeyboardTracking(False)
        self.ampl = QDoubleSpinBox()
        self.ampl.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.ampl.setDecimals(3)
        self.ampl.setSingleStep(0.1)
        self.ampl.setRange(-145.0, 30.0)
        self.ampl.setKeyboardTracking(False)
        self.att = QDoubleSpinBox()
        self.att.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.att.setDecimals(3)
        self.att.setSingleStep(0.1)
        self.att.setRange(-145.0, 30.0)
        self.att.setKeyboardTracking(False)
        layout.addWidget(self.freq, 2, 0)
        layout.addWidget(self.ampl, 2, 1)
        layout.addWidget(self.att, 4, 1)
        self.buttonSwitch = TextChangingButton(("I", "O"))
        layout.addWidget(self.buttonSwitch, 2, 2)
        self.setLayout(layout)

    def setPowerRange(self, powerrange):
        self.spinPower.setRange(*powerrange)

    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(*freqrange)

    def setPowerNoSignal(self, power):
        self.spinPower.blockSignals(True)
        self.spinPower.setValue(power)
        self.spinPower.blockSignals(False)

    def setFreqNoSignal(self, freq):
        self.spinFreq.blockSignals(True)
        self.spinFreq.setValue(freq)
        self.spinFreq.blockSignals(False)

    def setStateNoSignal(self, state):
        self.buttonSwitch.blockSignals(True)
        self.buttonSwitch.setChecked(state)
        self.buttonSwitch.setAppearance(state)
        self.buttonSwitch.blockSignals(False)

class AD9910_9910_channel(AD9910_channel_GUI):



if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(AD9910_channel)
