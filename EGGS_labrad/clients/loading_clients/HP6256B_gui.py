from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch


class HP6256B_gui(QFrame):
    """
    GUI for the HP6256B power supply controlled by the ARTIQ DAC.
    """

    def __init__(self, name=None, num=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.number = num
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(275, 225)
        self.makeLayout(name)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # title
        self.title = QLabel(title)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        # dac
        self.dac_label = QLabel('Output Voltage (V)')
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(2)
        self.dac.setSingleStep(0.01)
        self.dac.setRange(0, 850)
        self.dac.setKeyboardTracking(False)
        # ramp
        self.ramp_start = QPushButton('Ramp')
        self.ramp_start.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        self.ramp_target_label = QLabel('End Voltage (V)')
        self.ramp_target = QDoubleSpinBox()
        self.ramp_target.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.ramp_target.setDecimals(2)
        self.ramp_target.setSingleStep(0.01)
        self.ramp_target.setRange(0, 850)
        self.ramp_target.setKeyboardTracking(False)
        self.ramp_rate_label = QLabel('Ramp Rate (V/s)')
        self.ramp_rate = QDoubleSpinBox()
        self.ramp_rate.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.ramp_rate.setDecimals(2)
        self.ramp_rate.setSingleStep(0.01)
        self.ramp_rate.setRange(0, 10)
        self.ramp_rate.setKeyboardTracking(False)
        # buttons
        self.toggleswitch = TextChangingButton(("On", "Off"))
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = Lockswitch()
        self.lockswitch.setChecked(True)

        # add widgets to layout
        layout.addWidget(self.title, 0, 0, 1, 3)
        layout.addWidget(self.dac_label, 1, 0, 1, 2)
        layout.addWidget(self.dac, 2, 0, 1, 3)
        layout.addWidget(self.ramp_target_label, 3, 1)
        layout.addWidget(self.ramp_rate_label, 3, 2)
        layout.addWidget(self.ramp_start, 4, 0, 1, 1)
        layout.addWidget(self.ramp_target, 4, 1, 1, 1)
        layout.addWidget(self.ramp_rate, 4, 2, 1, 1)
        layout.addWidget(self.toggleswitch, 5, 0)
        layout.addWidget(self.lockswitch, 5, 1)
        layout.addWidget(self.resetswitch, 5, 2)
        # connect signal to slot
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

    @inlineCallbacks
    def lock(self, status):
        yield self.resetswitch.setEnabled(status)
        yield self.dac.setEnabled(status)



if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(HP6256B_gui, name='HP6256B Client')
