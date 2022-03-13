from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QFrame, QGridLayout, QPushButton, QDoubleSpinBox

from EGGS_labrad.clients.Widgets import TextChangingButton
from EGGS_labrad.clients.Widgets import QCustomProgressBar as MQProgressBar
from EGGS_labrad.clients.Widgets import QCustomSlideIndicator as SlideIndicator

import pyqtgraph as pg


class StretchedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.setMinimumSize(QtCore.QSize(350, 100))

    def resizeEvent(self, evt):
        font = self.font()
        font.setPixelSize(self.width() * 0.14 - 14)
        self.setFont(font)


class QCustomWavemeterChannel(QFrame):
    """
    GUI for an individual wavemeter channel.
    """

    def __init__(self, chanName, wmChannel, DACPort, frequency, stretchedlabel, displayPattern,
                 displayPIDvoltage=None, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(chanName, wmChannel, DACPort, frequency, stretchedlabel, displayPIDvoltage, displayPattern)

    def makeLayout(self, name, wmChannel, DACPort, frequency, stretchedlabel, displayPIDvoltage, displayPattern):
        layout = QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        chanName = QLabel(name)
        chanName.setFont(QFont(shell_font, pointSize=16))
        chanName.setAlignment(QtCore.Qt.AlignCenter)

        configtitle = QLabel('WLM Connections:')
        configtitle.setAlignment(QtCore.Qt.AlignBottom)
        configtitle.setFont(QFont(shell_font, pointSize=13))

        configLabel = QLabel("Channel " + str(wmChannel) + '        ' + "DAC Port " + str(DACPort))
        configLabel.setFont(QFont(shell_font, pointSize=8))
        configLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.PIDvoltage = QLabel('DAC Voltage (mV)  -.-')
        self.PIDvoltage.setFont(QFont(shell_font, pointSize=12))

        if displayPIDvoltage:
            self.PIDindicator = SlideIndicator([-10.0, 10.0])

        self.powermeter = MQProgressBar()
        self.powermeter.setOrientation(QtCore.Qt.Vertical)
        self.powermeter.setMeterColor("orange", "red")
        self.powermeter.setMeterBorder("orange")

        if displayPIDvoltage is True:
            layout.addWidget(self.PIDvoltage, 6, 6, 1, 5)
            layout.addWidget(self.PIDindicator, 5, 6, 1, 5)
        if stretchedlabel is True:
            self.currentfrequency = StretchedLabel(frequency)
        else:
            self.currentfrequency = QLabel(frequency)

        self.currentfrequency.setFont(QFont(shell_font, pointSize=60))
        self.currentfrequency.setAlignment(QtCore.Qt.AlignCenter)
        self.currentfrequency.setMinimumWidth(600)

        frequencylabel = QLabel('Set Frequency')
        frequencylabel.setAlignment(QtCore.Qt.AlignBottom)
        frequencylabel.setFont(QFont(shell_font, pointSize=13))

        exposurelabel = QLabel('Set Exposure (ms)')
        exposurelabel.setAlignment(QtCore.Qt.AlignBottom)
        exposurelabel.setFont(QFont(shell_font, pointSize=13))

        self.setPID = QPushButton('Set PID')
        self.setPID.setMaximumHeight(30)
        self.setPID.setFont(QFont(shell_font, pointSize=10))

        self.measSwitch = TextChangingButton('WLM Measure')
        self.lockChannel = TextChangingButton('Lock Channel')
        self.zeroVoltage = QPushButton('Zero Voltage')
        self.lockChannel.setMinimumWidth(180)

        # editable fields
        self.spinFreq = QDoubleSpinBox()
        self.spinFreq.setFont(QFont(shell_font, pointSize=16))
        self.spinFreq.setDecimals(6)
        self.spinFreq.setSingleStep(0.000001)
        self.spinFreq.setRange(100.0, 1000.0)
        self.spinFreq.setKeyboardTracking(False)

        self.spinExp = QDoubleSpinBox()
        self.spinExp.setFont(QFont(shell_font, pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        # 10 seconds is the max exposure time on the wavemeter.
        self.spinExp.setRange(0, 10000.0)
        self.spinExp.setKeyboardTracking(False)

        if displayPattern:
            pg.setConfigOption('background', 'w')
            self.plot1 = pg.PlotWidget(name='Plot 1')
            self.plot1.hideAxis('bottom')
            self.plot1.hideAxis('left')
            layout.addWidget(self.plot1, 7, 0, 1, 12)
            # self.plot2 = pg.PlotWidget(name='Plot 2')
            # self.plot2.hideAxis('bottom')
            # self.plot2.hideAxis('left')
            # layout.addWidget(self.plot2,        7, 1, 1, 11)

        layout.addWidget(self.spinFreq, 6, 0, 1, 1)
        layout.addWidget(self.spinExp, 6, 3, 1, 3)
        layout.addWidget(self.measSwitch, 0, 6, 1, 5)
        layout.addWidget(self.lockChannel, 1, 6, 1, 5)
        layout.addWidget(self.setPID, 2, 6, 1, 5)
        layout.addWidget(chanName, 0, 0, 1, 1)
        layout.addWidget(configtitle, 3, 6, 1, 5)
        layout.addWidget(configLabel, 4, 6, 1, 5)
        layout.addWidget(self.currentfrequency, 1, 0, 4, 1)
        layout.addWidget(frequencylabel, 5, 0, 1, 1)
        layout.addWidget(exposurelabel, 5, 3, 1, 3)
        layout.addWidget(self.powermeter, 0, 11, 7, 1)

        layout.minimumSize()
        self.setLayout(layout)

    def setExpRange(self, exprange):
        self.spinExp.setRange(exprange)

    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(freqrange)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(QCustomWavemeterChannel, chanName='Repumper', wmChannel=1,
                                    DACPort=4, frequency='Under Exposed',
                                    stretchedlabel=False, displayPattern=True)
