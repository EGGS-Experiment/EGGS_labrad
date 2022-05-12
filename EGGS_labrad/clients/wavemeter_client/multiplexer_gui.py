"""
Contains all the GUI elements needed for the multiplexer client.
"""
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QGridLayout, QGroupBox,\
                            QDesktopWidget, QPushButton, QDoubleSpinBox, QComboBox,\
                            QCheckBox, QScrollArea, QWidget

from EGGS_labrad.clients import wav2RGB
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomProgressBar, QCustomSlideIndicator, QClientMenuHeader


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

        # signal details
        status_label = QLabel('Status:')
        self.active_status = QLabel('Inactive')
        self.active_status.setStyleSheet('background-color: red')
        self.active_status.setFont(main_font)
        channelNum_label = QLabel('Channel:')
        self.channelNum = QLabel('N/A')
        self.channelNum.setFont(main_font)
        dacPort_label = QLabel('DAC Port:')
        self.dacPort_display = QLabel('N/A')
        self.dacPort_display.setFont(main_font)
        lock_freq_label = QLabel('Lock Frequency (THz):')
        self.lock_freq = QLabel('N/A')
        self.lock_freq.setFont(main_font)

        # labels
        inputLabel = QLabel('Details')
        inputLabel.setFont(header_font)
        PIDlabel = QLabel('PID Settings')
        PIDlabel.setFont(header_font)
        outLabel = QLabel('Output Settings')
        outLabel.setFont(header_font)
        vLabel = QLabel('Voltage Output')
        vLabel.setFont(header_font)

        pLabel = QLabel('Proportional:')
        iLabel = QLabel('Integral:')
        dLabel = QLabel('Derivative:')
        dtLabel = QLabel('dt (s):')
        factorLabel = QLabel('V:')
        exponentLabel = QLabel('GHz:')
        polarityLabel = QLabel('Polarity:')
        boundLabel = QLabel('Output Voltage Bounds:')
        boundLabel.setAlignment(Qt.AlignLeft)
        boundLabel.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        sensLabel = QLabel('Sensitivity (V/GHz):')
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
        self.useDTBox = QCheckBox('Const dt')
        #self.useDTBox.setCheckable(True)
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

        self.minBound_label = QLabel('Min (mV):')
        self.minBound_label.setFont(label_font)
        self.minBound = QDoubleSpinBox()
        self.minBound.setFont(main_font)
        self.minBound.setDecimals(0)
        self.minBound.setSingleStep(1)
        self.minBound.setRange(-5000, 0)
        self.minBound.setKeyboardTracking(False)

        self.maxBound_label = QLabel('Max (mV):')
        self.maxBound_label.setFont(label_font)
        self.maxBound = QDoubleSpinBox()
        self.maxBound.setFont(main_font)
        self.maxBound.setDecimals(0)
        self.maxBound.setSingleStep(1)
        self.maxBound.setRange(-5000, 0)
        self.maxBound.setKeyboardTracking(False)

        # voltage output
        self.PIDvoltage_label = QLabel('DAC Voltage (mV):')
        self.PIDvoltage_label.setFont(label_font)
        self.PIDvoltage = QLabel('0')
        self.PIDvoltage.setFont(main_font)
        self.PIDvoltage.setAlignment(Qt.AlignRight)
        self.PIDindicator = QCustomSlideIndicator([-10.0, 10.0])

        # set layout
        layout = QGridLayout(self)
        layout.minimumSize()

        # channel details
        layout.addWidget(inputLabel,            0, 0, 1, 1)
        layout.addWidget(status_label,          1, 0, 1, 1)
        layout.addWidget(self.active_status,    2, 0, 1, 1)
        layout.addWidget(channelNum_label,      3, 0, 1, 1)
        layout.addWidget(self.channelNum,       4, 0, 1, 1)
        layout.addWidget(dacPort_label,         5, 0, 1, 1)
        layout.addWidget(self.dacPort_display,  6, 0, 1, 1)
        layout.addWidget(lock_freq_label,       7, 0, 1, 1)
        layout.addWidget(self.lock_freq,        8, 0, 1, 1)

        # PID layout
        layout.addWidget(PIDlabel,              0, 2, 1, 2)
        layout.addWidget(pLabel,                1, 2, 1, 2)
        layout.addWidget(self.spinP,            2, 2, 1, 2)
        layout.addWidget(iLabel,                3, 2, 1, 2)
        layout.addWidget(self.spinI,            4, 2, 1, 2)
        layout.addWidget(dLabel,                5, 2, 1, 2)
        layout.addWidget(self.spinD,            6, 2, 1, 2)
        layout.addWidget(dtLabel,               7, 2, 1, 1)
        layout.addWidget(self.spinDt,           8, 2, 1, 1)
        layout.addWidget(self.useDTBox,         8, 3, 1, 1)

        # signal layout
        layout.addWidget(outLabel,              0, 4, 1, 2)
        layout.addWidget(polarityLabel,         1, 4, 1, 2)
        layout.addWidget(self.polarityBox,      2, 4, 1, 2)
        layout.addWidget(boundLabel,            3, 4, 1, 2)
        layout.addWidget(self.minBound_label,   4, 4, 1, 1)
        layout.addWidget(self.minBound,         5, 4, 1, 1)
        layout.addWidget(self.maxBound_label,   4, 5, 1, 1)
        layout.addWidget(self.maxBound,         5, 5, 1, 1)
        layout.addWidget(sensLabel,             6, 4, 1, 2)
        layout.addWidget(factorLabel,           7, 4, 1, 1)
        layout.addWidget(self.spinFactor,       8, 4, 1, 1)
        layout.addWidget(exponentLabel,         7, 5, 1, 1)
        layout.addWidget(self.spinExp,          8, 5, 1, 1)

        # voltage output layout
        layout.addWidget(vLabel,                0, 6, 1, 2)
        layout.addWidget(self.PIDvoltage_label, 1, 6, 1, 2)
        layout.addWidget(self.PIDvoltage,       2, 6, 1, 2)
        layout.addWidget(self.PIDindicator,     4, 6, 1, 2)

        # connect slots
        self.useDTBox.stateChanged.connect(lambda status: self.spinDt.setEnabled(status))
        self.useDTBox.click()
        self.useDTBox.click()


class multiplexer_channel(QFrame):
    """
    GUI for an individual wavemeter channel.
    """

    def __init__(self, chanName, wmChannel, DACPort, frequency,
                 displayPIDvoltage=None, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(chanName, wmChannel, DACPort, frequency, displayPIDvoltage)
        self.initializeGUI()

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
        currentfrequency_label = QLabel('Measured Frequency (THz):')
        self.currentfrequency = QLabel(frequency)
        self.currentfrequency.setFont(QFont(shell_font, pointSize=30))
        self.currentfrequency.setAlignment(Qt.AlignCenter)
        self.currentfrequency.setMinimumWidth(500)

        # power meter
        self.powermeter = QCustomProgressBar(max=4000, orientation=Qt.Vertical, border_color="orange",
                                             start_color="orange", end_color="red")
        self.powermeter.setAlignment(Qt.AlignCenter)
        self.powermeter_display = QLabel('0000')
        self.powermeter_display.setFont(QFont(shell_font, pointSize=12))
        self.powermeter_display.setAlignment(Qt.AlignLeft)

        # buttons
        self.measSwitch = TextChangingButton(('Stop Measuring', 'Start Measuring'))
        self.lockChannel = TextChangingButton(('Stop Locking', 'Start Locking'))
        self.lockChannel.setMinimumWidth(150)
        self.showTrace = TextChangingButton(('Hide Trace', 'Show Trace'))
        self.showTrace.setChecked(True)
        self.setPID = QPushButton('Set PID')
        self.setPID.setMaximumHeight(30)
        self.setPID.setFont(QFont(shell_font, pointSize=10))
        self.lockswitch = TextChangingButton(('Prevent Changes', 'Allow Changes'))
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.record_button.setMinimumHeight(25)

        # set frequency
        frequencylabel = QLabel('Lock Frequency (THz)')
        frequencylabel.setAlignment(Qt.AlignBottom)
        frequencylabel.setFont(QFont(shell_font, pointSize=10))
        self.spinFreq = QDoubleSpinBox()
        self.spinFreq.setFont(QFont(shell_font, pointSize=16))
        self.spinFreq.setDecimals(6)
        self.spinFreq.setSingleStep(0.000001)
        self.spinFreq.setRange(100.0, 1000.0)
        self.spinFreq.setKeyboardTracking(False)
        # exposure time
        exposurelabel = QLabel('Exposure Time (ms)')
        exposurelabel.setAlignment(Qt.AlignBottom)
        exposurelabel.setFont(QFont(shell_font, pointSize=10))
        self.spinExp = QDoubleSpinBox()
        self.spinExp.setFont(QFont(shell_font, pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        self.spinExp.setRange(0, 10000.0)
        self.spinExp.setKeyboardTracking(False)

        # lay out
        layout.addWidget(self.channel_header,       0, 0, 2, 3)
        layout.addWidget(currentfrequency_label,    1, 0, 2, 1)
        layout.addWidget(self.currentfrequency,     2, 0, 3, 3)
        layout.addWidget(frequencylabel,            5, 0, 1, 1)
        layout.addWidget(self.spinFreq,             6, 0, 1, 2)
        layout.addWidget(exposurelabel,             5, 2, 1, 1)
        layout.addWidget(self.spinExp,              6, 2, 1, 1)
        layout.addWidget(self.measSwitch,           0, 3, 1, 1)
        layout.addWidget(self.lockChannel,          1, 3, 1, 1)
        layout.addWidget(self.showTrace,            2, 3, 1, 1)
        layout.addWidget(self.setPID,               3, 3, 1, 1)
        layout.addWidget(self.record_button,        5, 3, 1, 1)
        layout.addWidget(self.lockswitch,           6, 3, 1, 1)
        layout.addWidget(self.powermeter,           0, 4, 6, 1)
        layout.addWidget(self.powermeter_display,   6, 4, 1, 1)

    def initializeGUI(self):
        self.lockswitch.toggled.connect(lambda status: self._lock(status))
        self.lockswitch.setChecked(True)

    def _lock(self, status):
        self.spinFreq.setEnabled(status)
        self.spinExp.setEnabled(status)
        self.measSwitch.setEnabled(status)
        self.lockChannel.setEnabled(status)


class multiplexer_gui(QFrame):
    """
    The full wavemeter GUI.
    """

    def __init__(self, chaninfo):
        super().__init__()
        # holder dicts
        self.chaninfo = chaninfo
        self.channels = {}
        self.dacPorts = {}
        self.pattern = {}
        # configure GUI
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle('Multiplexed Wavemeter')
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.makeLayout()

    def makeLayout(self):
        layout = QGridLayout(self)
        # wavemeter channels
        qBox_wm = QGroupBox('Wavemeter Channels')
        qBox_wm_layout = QGridLayout(qBox_wm)
            # wavemeter buttons
        self.startSwitch = TextChangingButton('Wavemeter')
        #self.startSwitch.setMaximumHeight(50)
        self.lockSwitch = TextChangingButton('Locking')
        self.lockSwitch.setMaximumHeight(50)
        qBox_wm_layout.addWidget(self.startSwitch, 0, 0)
        qBox_wm_layout.addWidget(self.lockSwitch, 0, 1)
            # holder for wavemeter channels
        wm_scroll = QScrollArea()
        wm_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        wmChan_widget = QWidget()
        wmChan_layout = QGridLayout(wmChan_widget)
        qBox_wm_layout.addWidget(wm_scroll, 1, 0, 1, 2)

        # PID
        qBox_PID = QGroupBox('Lock Settings')
        qBox_PID_layout = QGridLayout(qBox_PID)
        self.pidGUI = multiplexer_pid()
        self.pidGUI.setMaximumHeight(250)
        qBox_PID_layout.addWidget(self.pidGUI)

        # interferometer display
        qBox_intTrace = QGroupBox('Interferometer')
        qBox_intTrace_layout = QGridLayout(qBox_intTrace)
        pg.setConfigOption('background', 'k')
        # configure pyqtgraph
        pg.setConfigOption('antialias', False)
        from importlib.util import find_spec
        if find_spec('OpenGL'):
            pg.setConfigOption('useOpenGL', True)
            pg.setConfigOption('enableExperimental', True)
        # configure interferometer display
        self.trace_display = pg.PlotWidget(name='Interferometer Trace', border=True)
        self.trace_display.showGrid(x=True, y=True, alpha=0.5)
        self.trace_display.setLimits(xMin=0, xMax=2000, yMin=0, yMax=3e8)
        self.trace_display.setMinimumHeight(400)
        self.trace_display.setMaximumWidth(1000)
        self.trace_display_legend = self.trace_display.addLegend(size=(200, 200))
        qBox_intTrace_layout.addWidget(self.trace_display)
        # create channel widgets
        for chan_name, chan_params in self.chaninfo.items():
            wmChannel = chan_params[0]
            position = chan_params[2]
            widget = self._createChannel(chan_name, chan_params)
            widget.setMaximumHeight(200)
            # add to holders
            self.channels[wmChannel] = widget
            wmChan_layout.addWidget(self.channels[wmChannel], position[1], position[0], 1, 3)
        # add wavemeter channel holder to qBox
        wm_scroll.setWidget(wmChan_widget)
        wm_scroll.setMinimumWidth(wmChan_widget.sizeHint().width())
        # add title
        title = QLabel('Wavemeter Client')
        title.setFont(QFont('MS Shell Dlg 2', pointSize=18))
        title.setMaximumHeight(40)
        # create header
        self.header = QClientMenuHeader()
        # final layout
        layout.setMenuBar(self.header)
        layout.addWidget(title,             0, 0, 1, 2)
        layout.addWidget(qBox_wm,           1, 0, 4, 1)
        layout.addWidget(qBox_intTrace,     1, 1, 3, 1)
        layout.addWidget(qBox_PID,          4, 1, 1, 1)

    def _createChannel(self, name, params):
        # initialize widget
        wmChannel, frequency, _, displayPID, dacPort, rails = params
        widget = multiplexer_channel(name, wmChannel, dacPort, frequency, displayPID)
        widget.spinFreq.setValue(float(frequency))
        # get color of frequency
        wavelength = 2.998e8 / (float(frequency) * 1e3)
        color = wav2RGB(wavelength)
        widget.currentfrequency.setStyleSheet('color: rgb' + str(color))
        # create PlotDataItem (i.e. a trace) and add it to the legend
        self.pattern[wmChannel] = self.trace_display.plot(pen=pg.mkPen(color=color, width=3),
                                                          name="{:.0f}nm".format(wavelength),
                                                          skipFiniteCheck=True)
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
            self.showMaximized()
            pass

    def show(self):
        # make us showmaximized instead of normal show
        self.showMaximized()


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
