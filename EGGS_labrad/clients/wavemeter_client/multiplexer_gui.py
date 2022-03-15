"""
Contains all the GUI elements needed for the multiplexer client.
"""

import pyqtgraph as pg

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QGridLayout, QGroupBox, QDesktopWidget, QPushButton, QDoubleSpinBox, QComboBox, QCheckBox

from EGGS_labrad.clients.Widgets.wav2RGB import wav2RGB
from EGGS_labrad.clients.Widgets import TextChangingButton
from EGGS_labrad.clients.Widgets import QCustomProgressBar as MQProgressBar
from EGGS_labrad.clients.Widgets import QCustomSlideIndicator as SlideIndicator


class StretchedLabel(QLabel):
    """
    Creates a stretched label.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(QtCore.QSize(350, 100))

    def resizeEvent(self, evt):
        font = self.font()
        font.setPixelSize(self.width() * 0.14 - 14)
        self.setFont(font)


class multiplexer_pid(QFrame):

    def __init__(self, DACPort=0, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(DACPort)

    def makeLayout(self, DACPort):
        label_font = QFont('MS Shell Dlg 2', pointSize=8)
        label_alignment = Qt.AlignLeft
        main_font = QFont('MS Shell Dlg 2', pointSize=16)
        main_alignment = Qt.AlignRight

        # labels
        pLabel = QLabel('Proportional')
        iLabel = QLabel('Integral')
        dLabel = QLabel('Derivative')
        dtLabel = QLabel('dt (s)')
        factorLabel = QLabel('Factor (V)')
        exponentLabel = QLabel('THz*10^')
        polarityLabel = QLabel('Polarity')
        sensLabel = QLabel('PID Sensitivity')
        sensLabel.setAlignment(Qt.AlignCenter)
        sensLabel.setFont(label_font)

        for label in (pLabel, iLabel, dLabel, dtLabel, factorLabel, exponentLabel, polarityLabel):
            label.setFont(label_font)
            label.setAlignment(label_alignment)
            label.setAlignment(Qt.AlignBottom)

        # PID control
        self.spinP = QDoubleSpinBox()
        self.spinI = QDoubleSpinBox()
        self.spinD = QDoubleSpinBox()
        self.spinDt = QDoubleSpinBox()

        for spinbox in (self.spinP, self.spinI, self.spinD, self.spinDt):
            spinbox.setFont(main_font)
            spinbox.setDecimals(3)
            spinbox.setSingleStep(0.001)
            spinbox.setRange(0, 100)
            spinbox.setKeyboardTracking(False)

        # other control elements
        self.spinFactor = QDoubleSpinBox()
        self.spinFactor.setFont(main_font)
        self.spinFactor.setDecimals(2)
        self.spinFactor.setSingleStep(0.01)
        self.spinFactor.setRange(0, 9.99)
        self.spinFactor.setKeyboardTracking(False)

        self.spinExp = QDoubleSpinBox()
        self.spinExp.setFont(main_font)
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        self.spinExp.setRange(-6, 3)
        self.spinExp.setKeyboardTracking(False)

        self.polarityBox = QComboBox(self)
        self.polarityBox.addItem("Positive")
        self.polarityBox.addItem("Negative")

        self.useDTBox = QCheckBox('Use Const dt')
        self.useDTBox.setFont(main_font)

        # set layout
        layout = QGridLayout()
        layout.minimumSize()

        layout.addWidget(pLabel, 0, 0, 1, 1)
        layout.addWidget(self.spinP, 1, 0, 1, 1)
        layout.addWidget(iLabel, 2, 0, 1, 1)
        layout.addWidget(self.spinI, 3, 0, 1, 1)
        layout.addWidget(dLabel, 4, 0, 1, 1)
        layout.addWidget(self.spinD, 5, 0, 1, 1)

        layout.addWidget(self.useDTBox, 0, 1, 1, 1)
        layout.addWidget(dtLabel, 1, 1, 1, 1)
        layout.addWidget(self.spinDt, 3, 1, 1, 1)
        layout.addWidget(polarityLabel, 4, 1, 1, 1)
        layout.addWidget(self.polarityBox, 5, 1, 1, 1)

        layout.addWidget(sensLabel, 0, 2, 1, 1)
        layout.addWidget(factorLabel, 1, 2, 1, 1)
        layout.addWidget(self.spinFactor, 2, 2, 1, 1)
        layout.addWidget(exponentLabel, 3, 2, 1, 1)
        layout.addWidget(self.spinExp, 4, 2, 1, 1)

        self.setLayout(layout)


class multiplexer_channel(QFrame):
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

        configLabel = QLabel("Channel: " + str(wmChannel) + '        ' + "DAC Port: " + str(DACPort))
        configLabel.setFont(QFont(shell_font, pointSize=8))
        configLabel.setAlignment(QtCore.Qt.AlignLeft)
        configLabel.setAlignment(QtCore.Qt.AlignTop)

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

        frequencylabel = QLabel('Lock Frequency')
        frequencylabel.setAlignment(QtCore.Qt.AlignBottom)
        frequencylabel.setFont(QFont(shell_font, pointSize=13))

        exposurelabel = QLabel('Exposure Time (ms)')
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

        layout.addWidget(configLabel, 0, 0)
        layout.addWidget(chanName, 0, 0, 1, 1)

        layout.addWidget(self.spinFreq, 6, 0, 1, 1)
        layout.addWidget(self.spinExp, 6, 3, 1, 3)
        layout.addWidget(self.measSwitch, 0, 6, 1, 5)
        layout.addWidget(self.lockChannel, 1, 6, 1, 5)
        layout.addWidget(self.setPID, 2, 6, 1, 5)

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


class multiplexer_gui(QFrame):

    def __init__(self, chaninfo):
        super().__init__()
        self.chaninfo = chaninfo
        self.channels = {}
        self.dacPorts = {}
        self.pattern = {}

        self.setWindowTitle('Multiplexed Wavemeter')
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._check_window_size()
        self.initializeGUI()

    def initializeGUI(self):
        # set up layouts
        layout = QGridLayout()
        subLayout = QGridLayout()
        qBox = QGroupBox('Wavelength and Lock settings')
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        # lock switches
        self.lockSwitch = TextChangingButton('Lock Wave Meter')
        self.lockSwitch.setMaximumHeight(50)
        self.startSwitch = TextChangingButton('Wavemeter')
        self.startSwitch.setMaximumHeight(50)
        subLayout.addWidget(self.lockSwitch, 0, 2)
        subLayout.addWidget(self.startSwitch, 0, 0)

        # create channel widgets
        for chan_name, chan_params in self.chaninfo.items():
            wmChannel = chan_params[0]
            position = chan_params[2]
            widget = self._createChannel(chan_name, chan_params)
            # add to holders
            self.channels[wmChannel] = widget
            subLayout.addWidget(self.channels[wmChannel], position[1], position[0], 1, 3)

        self.setLayout(layout)

    def _createChannel(self, name, params):
        # initialize widget
        wmChannel, frequency, _, stretched, displayPID, dacPort, rails, displayPattern = params
        print(displayPattern)
        widget = multiplexer_channel(name, wmChannel, dacPort, frequency, stretched, displayPattern, displayPID)

        # display PID
        if displayPID:
            try:
                widget.PIDindicator.set_rails(rails)
            except Exception as e:
                widget.PIDindicator.set_rails([-10.0, 10.0])

        # get color of frequency
        color = wav2RGB(2.998e8 / (float(frequency) * 1e3))
        widget.currentfrequency.setStyleSheet('color: rgb' + str(color))
        if displayPattern:
            # save handle in a dict for convenience
            # todo: remove pg from pyqtgraph stuff
            self.pattern[wmChannel] = widget.plot1.plot(pen=pg.mkPen(color=color))

        # dacPort
        if dacPort != 0:
            self.dacPorts[dacPort] = wmChannel
            widget.setPID.clicked.connect(lambda state=widget.setPID.isDown(), chan=name, dacPort=dacPort:
                                          self._initializePIDGUI(dacPort, chan))
        else:
            widget.spinFreq.setValue(float(frequency))

        return widget

    def _initializePIDGUI(self, dacPort, chan):
        self.pid = multiplexer_pid(dacPort)
        self.pid.setWindowTitle(chan + ' PID Settings')
        self.pid.move(self.pos())
        self.index = {1: 0, -1: 1}
        self.pid.show()

    def _check_window_size(self):
        """
        Checks screen size to make sure window fits in the screen.
        """
        desktop = QDesktopWidget()
        screensize = desktop.availableGeometry()
        width = screensize.width()
        height = screensize.height()
        min_pixel_size = 1080
        if (width <= min_pixel_size) or (height <= min_pixel_size):
            self.showMaximized()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run multiplexer PID gui
    # runGUI(multiplexer_pid)

    # run multiplexer channel GUI
    #runGUI(multiplexer_channel, chanName='Repumper', wmChannel=1,
                                 #DACPort=4, frequency='Under Exposed',
                                 #stretchedlabel=False, displayPattern=True)

    # run multiplexer client GUI
    from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
    runGUI(multiplexer_gui, multiplexer_config.channels)
