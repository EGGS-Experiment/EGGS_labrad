"""
Contains all the GUI elements needed for the multiplexer client.
"""

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QGridLayout, QGroupBox,\
                            QDesktopWidget, QPushButton, QDoubleSpinBox, QComboBox,\
                            QCheckBox, QScrollArea, QWidget, QVBoxLayout

from EGGS_labrad.clients.Widgets.wav2RGB import wav2RGB
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomProgressBar, QCustomSlideIndicator


class multiplexer_pid(QFrame):
    """
    GUI for the wavemeter PID frequency lock.
    """

    def __init__(self, DACPort=0, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(DACPort)

    def makeLayout(self, DACPort):
        label_font = QFont('MS Shell Dlg 2', pointSize=8)
        label_alignment = Qt.AlignLeft
        main_font = QFont('MS Shell Dlg 2', pointSize=14)
        header_font = QFont('MS Shell Dlg 2', pointSize=12)

        # labels
        PIDlabel = QLabel('PID Settings')
        PIDlabel.setFont(header_font)
        outLabel = QLabel('Output Settings')
        outLabel.setFont(header_font)
        vLabel = QLabel('Voltage Output')
        vLabel.setFont(header_font)

        pLabel = QLabel('Proportional')
        iLabel = QLabel('Integral')
        dLabel = QLabel('Derivative')
        dtLabel = QLabel('dt (s)')
        factorLabel = QLabel('V')
        exponentLabel = QLabel('GHz')
        polarityLabel = QLabel('Polarity')
        sensLabel = QLabel('Sensitivity (V/GHz): ')
        sensLabel.setAlignment(Qt.AlignLeft)
        sensLabel.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        for label in (pLabel, iLabel, dLabel, dtLabel, factorLabel, exponentLabel, polarityLabel):
            label.setFont(label_font)
            label.setAlignment(label_alignment)
            label.setAlignment(Qt.AlignBottom)

        # PID control
        self.spinP = QDoubleSpinBox()
        self.spinI = QDoubleSpinBox()
        self.spinD = QDoubleSpinBox()
        self.spinDt = QDoubleSpinBox()
        self.useDTBox = QCheckBox('Use Const dt')
        self.useDTBox.setFont(QFont('MS Shell Dlg 2', pointSize=12))

        for spinbox in (self.spinP, self.spinI, self.spinD, self.spinDt):
            spinbox.setFont(main_font)
            spinbox.setDecimals(3)
            spinbox.setSingleStep(0.001)
            spinbox.setRange(0, 100)
            spinbox.setKeyboardTracking(False)

        # output signal
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
        self.polarityBox.setFont(main_font)

        self.minBound_label = QLabel('Min (mV)')
        self.minBound_label.setFont(label_font)
        self.minBound = QDoubleSpinBox()
        self.minBound.setFont(main_font)
        self.minBound.setDecimals(0)
        self.minBound.setSingleStep(1)
        self.minBound.setRange(-5000, 0)
        self.minBound.setKeyboardTracking(False)

        self.maxBound_label = QLabel('Max (mV)')
        self.maxBound_label.setFont(label_font)
        self.maxBound = QDoubleSpinBox()
        self.maxBound.setFont(main_font)
        self.maxBound.setDecimals(0)
        self.maxBound.setSingleStep(1)
        self.maxBound.setRange(-5000, 0)
        self.maxBound.setKeyboardTracking(False)

        # voltage output
        self.PIDindicator = QCustomSlideIndicator([-10.0, 10.0])
        self.PIDvoltage_label = QLabel('DAC Voltage (mV)')
        self.PIDvoltage_label.setFont(label_font)
        self.PIDvoltage = QLabel('0000')
        self.PIDvoltage.setFont(main_font)

        # set layout
        layout = QGridLayout(self)
        layout.minimumSize()

        # PID layout
        layout.addWidget(PIDlabel,              0, 0, 1, 2)
        layout.addWidget(pLabel,                1, 0, 1, 2)
        layout.addWidget(self.spinP,            2, 0, 1, 2)
        layout.addWidget(iLabel,                3, 0, 1, 2)
        layout.addWidget(self.spinI,            4, 0, 1, 2)
        layout.addWidget(dLabel,                5, 0, 1, 2)
        layout.addWidget(self.spinD,            6, 0, 1, 2)
        layout.addWidget(dtLabel,               7, 0, 1, 1)
        layout.addWidget(self.spinDt,           8, 0, 1, 1)
        layout.addWidget(self.useDTBox,         8, 1, 1, 1)

        # signal layout
        layout.addWidget(outLabel,              0, 2, 1, 2)
        layout.addWidget(polarityLabel,         1, 2, 1, 2)
        layout.addWidget(self.polarityBox,      2, 2, 1, 2)
        layout.addWidget(self.minBound_label,   3, 2, 1, 1)
        layout.addWidget(self.minBound,         4, 2, 1, 1)
        layout.addWidget(self.maxBound_label,   3, 3, 1, 1)
        layout.addWidget(self.maxBound,         4, 3, 1, 1)
        layout.addWidget(sensLabel,             5, 2, 1, 2)
        layout.addWidget(factorLabel,           6, 2, 1, 1)
        layout.addWidget(self.spinFactor,       7, 2, 1, 1)
        layout.addWidget(exponentLabel,         6, 3, 1, 1)
        layout.addWidget(self.spinExp,          7, 3, 1, 1)

        # voltage output layout
        layout.addWidget(vLabel,                0, 4, 1, 2)
        layout.addWidget(self.PIDindicator,     1, 4, 1, 2)
        layout.addWidget(self.PIDvoltage_label, 2, 4, 1, 2)
        layout.addWidget(self.PIDvoltage,       3, 4, 1, 2)



class multiplexer_channel(QFrame):
    """
    GUI for an individual wavemeter channel.
    """

    def __init__(self, chanName, wmChannel, DACPort, frequency,
                 displayPIDvoltage=None, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(chanName, wmChannel, DACPort, frequency, displayPIDvoltage)

    def makeLayout(self, name, wmChannel, DACPort, frequency, displayPIDvoltage):
        layout = QGridLayout(self)
        layout.minimumSize()
        shell_font = 'MS Shell Dlg 2'

        # channel header
        self.channel_header = QWidget()
        channel_header_layout = QGridLayout(self.channel_header)

        chanName = QLabel(name)
        chanName.setFont(QFont(shell_font, pointSize=17))
        chanName.setAlignment(Qt.AlignCenter)
        channel_label = QLabel("Channel: {:d}".format(wmChannel))
        channel_label.setFont(QFont(shell_font, pointSize=8))
        channel_label.setAlignment(Qt.AlignLeft)
        channel_label.setAlignment(Qt.AlignBottom)
        dacPort_label = QLabel("DAC Port: {:d}".format(DACPort))
        dacPort_label.setFont(QFont(shell_font, pointSize=8))
        dacPort_label.setAlignment(Qt.AlignLeft)
        dacPort_label.setAlignment(Qt.AlignTop)

        channel_header_layout.addWidget(channel_label,  0, 0, 1, 1)
        channel_header_layout.addWidget(dacPort_label,  1, 0, 1, 1)
        channel_header_layout.addWidget(chanName,       0, 0, 3, 1)

        # display frequency
        self.currentfrequency = QLabel(frequency)
        self.currentfrequency.setFont(QFont(shell_font, pointSize=30))
        self.currentfrequency.setAlignment(Qt.AlignCenter)
        self.currentfrequency.setMinimumWidth(300)

        # power meter
        self.powermeter = QCustomProgressBar()
        self.powermeter.setOrientation(Qt.Vertical)
        self.powermeter.setMeterColor("orange", "red")
        self.powermeter.setMeterBorder("orange")

        # PID
        self.setPID = QPushButton('Set PID')
        self.setPID.setMaximumHeight(30)
        self.setPID.setFont(QFont(shell_font, pointSize=10))

        # buttons
        self.measSwitch = TextChangingButton(('Stop Measuring', 'Start Measuring'))
        self.lockChannel = TextChangingButton(('Stop Locking', 'Start Locking'))
        self.lockChannel.setMinimumWidth(150)
        self.showTrace = TextChangingButton(('Hide Trace', 'Show Trace'))
        self.showTrace.setChecked(True)

        # set frequency
        self.frequencylabel = QLabel('Lock Frequency (THz)')
        self.frequencylabel.setAlignment(Qt.AlignBottom)
        self.frequencylabel.setFont(QFont(shell_font, pointSize=10))
        self.spinFreq = QDoubleSpinBox()
        self.spinFreq.setFont(QFont(shell_font, pointSize=16))
        self.spinFreq.setDecimals(6)
        self.spinFreq.setSingleStep(0.000001)
        self.spinFreq.setRange(100.0, 1000.0)
        self.spinFreq.setKeyboardTracking(False)

        # exposure time
        self.exposurelabel = QLabel('Exposure Time (ms)')
        self.exposurelabel.setAlignment(Qt.AlignBottom)
        self.exposurelabel.setFont(QFont(shell_font, pointSize=10))
        self.spinExp = QDoubleSpinBox()
        self.spinExp.setFont(QFont(shell_font, pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        self.spinExp.setRange(0, 10000.0)
        self.spinExp.setKeyboardTracking(False)

        # if displayPIDvoltage is True:
        #     self.PIDindicator = QCustomSlideIndicator([-10.0, 10.0])
        #     self.PIDvoltage = QLabel('DAC Voltage (mV)  -.-')
        #     self.PIDvoltage.setFont(QFont(shell_font, pointSize=12))
        #     layout.addWidget(self.PIDvoltage, 6, 6, 1, 5)
        #     layout.addWidget(self.PIDindicator, 5, 6, 1, 5)

        # lay out
        layout.addWidget(self.channel_header,   0, 0, 2, 1)
        layout.addWidget(self.currentfrequency, 1, 0, 3, 1)
        layout.addWidget(self.frequencylabel,   5, 0, 1, 1)
        layout.addWidget(self.spinFreq,         6, 0, 1, 1)
        layout.addWidget(self.exposurelabel,    5, 3, 1, 1)
        layout.addWidget(self.spinExp,          6, 3, 1, 1)
        layout.addWidget(self.measSwitch,       0, 3, 1, 1)
        layout.addWidget(self.lockChannel,      1, 3, 1, 1)
        layout.addWidget(self.showTrace,        2, 3, 1, 1)
        layout.addWidget(self.setPID,           3, 3, 1, 1)
        layout.addWidget(self.powermeter,       0, 4, 7, 1)


class multiplexer_gui(QFrame):
    """
    The full wavemeter GUI.
    """

    def __init__(self, chaninfo):
        super().__init__()
        self.chaninfo = chaninfo
        self.channels = {}
        self.dacPorts = {}
        self.pattern = {}

        self.setWindowTitle('Multiplexed Wavemeter')
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._check_window_size()
        self.makeLayout()

    def makeLayout(self):
        label_font = QFont('MS Shell Dlg 2', pointSize=12)
        layout = QGridLayout(self)

        # wavemeter channels
        self.wm_label = QLabel('Wavemeter Channels')
        self.wm_label.setFont(label_font)
        #qBox = QGroupBox('Wavelength and Lock settings')
        qBox = QFrame()
        qBox.setFrameStyle(0x0001 | 0x0030)
        subLayout = QGridLayout(qBox)
        #self.channel_scroll = QScrollArea()
        #self.channel_scroll.setWidget(qBox)

        self.startSwitch = TextChangingButton('Wavemeter')
        self.startSwitch.setMaximumHeight(50)
        self.lockSwitch = TextChangingButton('Locking')
        self.lockSwitch.setMaximumHeight(50)
        subLayout.addWidget(self.startSwitch, 0, 0)
        subLayout.addWidget(self.lockSwitch, 0, 2)

        # PID
        self.pidGUI_label = QLabel('Lock Settings')
        self.pidGUI_label.setFont(label_font)
        self.pidGUI = multiplexer_pid()
        self.pidGUI.setMaximumHeight(200)

        # interferometer display
        #interferometer_wrapper = QWidget()
        #interferometer_layout = QVBoxLayout(interferometer_wrapper)
        pg.setConfigOption('background', 'k')
        self.trace_display_label = QLabel('Interferometer')
        self.trace_display_label.setFont(label_font)
        self.trace_display = pg.PlotWidget(name='Interferometer Trace', border=True)
        self.trace_display.showGrid(x=True, y=True, alpha=0.5)
        self.trace_display.setRange(yRange=[0, 2e8])
        self.trace_display.setMinimumHeight(400)
        self.trace_display.setMinimumWidth(400)

        # create channel widgets
        for chan_name, chan_params in self.chaninfo.items():
            wmChannel = chan_params[0]
            position = chan_params[2]
            widget = self._createChannel(chan_name, chan_params)
            widget.setMaximumHeight(200)
            # add to holders
            self.channels[wmChannel] = widget
            subLayout.addWidget(self.channels[wmChannel], position[1], position[0], 1, 3)

        layout.addWidget(self.wm_label, 0, 0)
        layout.addWidget(qBox, 1, 0, 4, 1)
        layout.addWidget(self.trace_display_label, 0, 1)
        layout.addWidget(self.trace_display, 1, 1)
        layout.addWidget(self.pidGUI_label, 2, 1)
        layout.addWidget(self.pidGUI, 3, 1)

    def _createChannel(self, name, params):
        # initialize widget
        wmChannel, frequency, _, displayPID, dacPort, rails = params
        widget = multiplexer_channel(name, wmChannel, dacPort, frequency, displayPID)
        widget.spinFreq.setValue(float(frequency))

        # display PID
        # try:
        #     widget.PIDindicator.set_rails(rails)
        # except Exception as e:
        #     widget.PIDindicator.set_rails([-10.0, 10.0])

        # get color of frequency
        color = wav2RGB(2.998e8 / (float(frequency) * 1e3))
        widget.currentfrequency.setStyleSheet('color: rgb' + str(color))
        self.pattern[wmChannel] = self.trace_display.plot(pen=pg.mkPen(color=color))

        # dacPort
        if dacPort != 0:
            self.dacPorts[dacPort] = wmChannel

        return widget

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
            #self.showMaximized()
            pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run multiplexer PID gui
    #runGUI(multiplexer_pid)

    # run multiplexer channel GUI
    #runGUI(multiplexer_channel, chanName='Repumper', wmChannel=1,
                                 #DACPort=4, frequency='Under Exposed')

    # run multiplexer client GUI
    from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
    runGUI(multiplexer_gui, multiplexer_config.channels)
