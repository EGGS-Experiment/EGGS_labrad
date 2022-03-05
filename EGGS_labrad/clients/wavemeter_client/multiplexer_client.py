from EGGS_labrad.clients import GUIClient
from twisted.internet.defer import inlineCallbacks, returnValue

try:
    from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
except Exception as e:
    pass

from common.lib.clients.qtui.multiplexerPID import QCustomPID
from common.lib.clients.qtui.multiplexerchannel import QCustomWavemeterChannel

import socket
import os
import pyqtgraph as pg
import numpy as np

SIGNALID1 = 445566
SIGNALID2 = 143533
SIGNALID3 = 111221
SIGNALID4 = 549210
SIGNALID5 = 190909
SIGNALID6 = 102588
SIGNALID7 = 148323
SIGNALID8 = 238883
SIGNALID9 = 462917


# this is the signal for the updated frequencies

class multiplexer_client(GUIClient):

    def getgui(self):
        if self.gui is None:
            self.gui = multiplexer_gui()
        return self.gui

    def __init__(self, reactor, parent=None):
        """
        initialized the GUI creates the reactor
        and empty dictionary for channel widgets to
        be stored for iteration. also grabs chan info
        from multiplexer_config
        """
        super(multiplexer_client, self).__init__()
        self.password = os.environ['LABRADPASSWORD']
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.name = socket.gethostname() + ' Wave Meter Client'
        self.d = {}
        self.wmChannels = {}
        self.connect()
        self._check_window_size()
        self.pattern_1 = {}
        self.pattern_2 = {}

    def _check_window_size(self):
        """Checks screen size to make sure window fits in the screen. """
        desktop = QtGui.QDesktopWidget()
        screensize = desktop.availableGeometry()
        width = screensize.width()
        height = screensize.height()
        min_pixel_size = 1080
        if (width <= min_pixel_size or height <= min_pixel_size):
            self.showMaximized()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relavent functions

        """
        self.chaninfo = multiplexer_config.info
        self.wavemeterIP = multiplexer_config.ip
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(self.wavemeterIP,
                                      name=self.name,
                                      password=self.password)

        self.server = yield self.cxn.multiplexerserver
        yield self.server.signal__frequency_changed(SIGNALID1)
        yield self.server.signal__selected_channels_changed(SIGNALID2)
        yield self.server.signal__update_exp(SIGNALID3)
        yield self.server.signal__lock_changed(SIGNALID4)
        yield self.server.signal__output_changed(SIGNALID5)
        yield self.server.signal__pidvoltage_changed(SIGNALID6)
        yield self.server.signal__channel_lock_changed(SIGNALID7)
        yield self.server.signal__amplitude_changed(SIGNALID8)
        yield self.server.signal__pattern_changed(SIGNALID9)

        yield self.server.addListener(listener=self.updateFrequency, source=None, ID=SIGNALID1)
        yield self.server.addListener(listener=self.toggleMeas, source=None, ID=SIGNALID2)
        yield self.server.addListener(listener=self.updateexp, source=None, ID=SIGNALID3)
        yield self.server.addListener(listener=self.toggleLock, source=None, ID=SIGNALID4)
        yield self.server.addListener(listener=self.updateWLMOutput, source=None, ID=SIGNALID5)
        yield self.server.addListener(listener=self.updatePIDvoltage, source=None, ID=SIGNALID6)
        yield self.server.addListener(listener=self.toggleChannelLock, source=None, ID=SIGNALID7)
        yield self.server.addListener(listener=self.updateAmplitude, source=None, ID=SIGNALID8)
        yield self.server.addListener(listener=self.updatePattern, source=None, ID=SIGNALID9)

        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):

        layout = QtGui.QGridLayout()

        self.setWindowTitle('Multiplexed wavemeter_client')

        qBox = QtGui.QGroupBox('Wave Length and Lock settings')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        self.lockSwitch = TextChangingButton('Lock Wave Meter')
        self.lockSwitch.setMaximumHeight(50)
        self.startSwitch = TextChangingButton('wavemeter_client')
        self.startSwitch.setMaximumHeight(50)
        initstartvalue = yield self.server.get_wlm_output()
        initlockvalue = yield self.server.get_lock_state()
        self.lockSwitch.setChecked(initlockvalue)
        self.startSwitch.setChecked(initstartvalue)

        self.lockSwitch.toggled.connect(self.setLock)
        self.startSwitch.toggled.connect(self.setOutput)

        subLayout.addWidget(self.lockSwitch, 0, 2)
        subLayout.addWidget(self.startSwitch, 0, 0)

        for chan in self.chaninfo:
            wmChannel = self.chaninfo[chan][0]
            hint = self.chaninfo[chan][1]
            position = self.chaninfo[chan][2]
            stretched = self.chaninfo[chan][3]
            displayPID = self.chaninfo[chan][4]
            dacPort = self.chaninfo[chan][5]
            displayPattern = self.chaninfo[chan][7]
            widget = QCustomWavemeterChannel(chan, wmChannel, dacPort, hint, stretched, displayPattern, displayPID)

            if displayPID:
                try:
                    rails = self.chaninfo[chan][6]
                    widget.PIDindicator.set_rails(rails)
                except:
                    rails = [-10.0, 10.0]
                    widget.PIDindicator.set_rails(rails)
            from common.lib.clients.qtui import RGBconverter as RGB
            RGB = RGB.RGBconverter()
            color = int(2.998e8 / (float(hint) * 1e3))
            color = RGB.wav2RGB(color)
            color = tuple(color)

            if dacPort != 0:
                self.wmChannels[dacPort] = wmChannel
                initcourse = yield self.getPIDCourse(dacPort, hint)
                widget.spinFreq.setValue(initcourse)
                widget.spinFreq.valueChanged.connect(
                    lambda freq=widget.spinFreq.value(), dacPort=dacPort: self.freqChanged(freq, dacPort))
                widget.setPID.clicked.connect(
                    lambda state=widget.setPID.isDown(), chan=chan, dacPort=dacPort: self.InitializePIDGUI(dacPort,
                                                                                                           chan))
                initLock = yield self.server.get_channel_lock(dacPort, wmChannel)
                widget.lockChannel.setChecked(bool(initLock))
                widget.lockChannel.toggled.connect(
                    lambda state=widget.lockChannel.isDown(), dacPort=dacPort: self.lockSingleChannel(state, dacPort))
            else:
                widget.spinFreq.setValue(float(hint))
                widget.lockChannel.toggled.connect(
                    lambda state=widget.lockChannel.isDown(), wmChannel=wmChannel: self.setButtonOff(wmChannel))

            if displayPattern:
                # save the widget hanlde in a dictionay here so we don't have to 
                # keeping recalculating the color later
                self.pattern_1[wmChannel] = widget.plot1.plot(pen=pg.mkPen(color=color))

            widget.currentfrequency.setStyleSheet('color: rgb' + str(color))
            widget.spinExp.valueChanged.connect(
                lambda exp=widget.spinExp.value(), wmChannel=wmChannel: self.expChanged(exp, wmChannel))
            initvalue = yield self.server.get_exposure(wmChannel)
            widget.spinExp.setValue(initvalue)
            initmeas = yield self.server.get_switcher_signal_state(wmChannel)
            initmeas = initmeas
            widget.measSwitch.setChecked(bool(initmeas))
            widget.measSwitch.toggled.connect(
                lambda state=widget.measSwitch.isDown(), wmChannel=wmChannel: self.changeState(state, wmChannel))

            self.d[wmChannel] = widget
            subLayout.addWidget(self.d[wmChannel], position[1], position[0], 1, 3)

        self.setLayout(layout)

    @inlineCallbacks
    def InitializePIDGUI(self, dacPort, chan):
        self.pid = QCustomPID(dacPort)
        self.pid.setWindowTitle(chan + ' PID settings')
        self.pid.move(self.pos())
        self.index = {1: 0, -1: 1}

        pInit = yield self.server.get_pid_p(dacPort)
        iInit = yield self.server.get_pid_i(dacPort)
        dInit = yield self.server.get_pid_d(dacPort)
        dtInit = yield self.server.get_pid_dt(dacPort)
        constInit = yield self.server.get_const_dt(dacPort)
        sensInit = yield self.server.get_pid_sensitivity(dacPort)
        polInit = yield self.server.get_pid_polarity(dacPort)

        self.pid.spinP.setValue(pInit)
        self.pid.spinI.setValue(iInit)
        self.pid.spinD.setValue(dInit)
        self.pid.spinDt.setValue(dtInit)
        self.pid.useDTBox.setCheckState(bool(constInit))
        self.pid.spinFactor.setValue(sensInit[0])
        self.pid.spinExp.setValue(sensInit[1])
        self.pid.polarityBox.setCurrentIndex(self.index[polInit])

        self.pid.spinP.valueChanged.connect(lambda p=self.pid.spinP.value(), dacPort=dacPort: self.changeP(p, dacPort))
        self.pid.spinI.valueChanged.connect(lambda i=self.pid.spinI.value(), dacPort=dacPort: self.changeI(i, dacPort))
        self.pid.spinD.valueChanged.connect(lambda d=self.pid.spinD.value(), dacPort=dacPort: self.changeD(d, dacPort))
        self.pid.spinDt.valueChanged.connect(
            lambda dt=self.pid.spinDt.value(), dacPort=dacPort: self.changeDt(dt, dacPort))
        self.pid.useDTBox.stateChanged.connect(
            lambda state=self.pid.useDTBox.isChecked(), dacPort=dacPort: self.constDt(state, dacPort))
        self.pid.spinFactor.valueChanged.connect(
            lambda factor=self.pid.spinFactor.value(), dacPort=dacPort: self.changeFactor(factor, dacPort))
        self.pid.spinExp.valueChanged.connect(
            lambda exponent=self.pid.spinExp.value(), dacPort=dacPort: self.changeExponent(exponent, dacPort))
        self.pid.polarityBox.currentIndexChanged.connect(
            lambda index=self.pid.polarityBox.currentIndex(), dacPort=dacPort: self.changePolarity(index, dacPort))

        self.pid.show()

    @inlineCallbacks
    def expChanged(self, exp, chan):
        # these are switched, dont know why
        exp = int(exp)
        yield self.server.set_exposure_time(chan, exp)

    def updateFrequency(self, c, signal):
        chan = signal[0]
        if chan in self.d:
            freq = signal[1]

            if not self.d[chan].measSwitch.isChecked():
                self.d[chan].currentfrequency.setText('Not Measured')
            elif freq == -3.0:
                self.d[chan].currentfrequency.setText('Under Exposed')
            elif freq == -4.0:
                self.d[chan].currentfrequency.setText('Over Exposed')
            elif freq == -17.0:
                self.d[chan].currentfrequency.setText('Data Error')
            else:
                self.d[chan].currentfrequency.setText(str(freq)[0:10])

    def updatePIDvoltage(self, c, signal):
        dacPort = signal[0]
        value = signal[1]
        if dacPort in self.wmChannels:
            try:
                self.d[self.wmChannels[dacPort]].PIDvoltage.setText('DAC Voltage (mV)  ' + "{:.1f}".format(value))
                self.d[self.wmChannels[dacPort]].PIDindicator.update_slider(value / 1000.0)
            except:
                pass

    def toggleMeas(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].measSwitch.blockSignals(True)
            self.d[chan].measSwitch.setChecked(value)
            self.d[chan].measSwitch.blockSignals(False)

    def toggleLock(self, c, signal):
        self.lockSwitch.blockSignals(True)
        self.lockSwitch.setChecked(signal)
        self.lockSwitch.blockSignals(False)

    def toggleChannelLock(self, c, signal):
        wmChannel = signal[1]
        state = signal[2]
        if wmChannel in self.d:
            self.d[wmChannel].lockChannel.blockSignals(True)
            self.d[wmChannel].lockChannel.setChecked(bool(state))
            self.d[wmChannel].lockChannel.blockSignals(False)

    def updateexp(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].spinExp.blockSignals(True)
            self.d[chan].spinExp.setValue(value)
            self.d[chan].spinExp.blockSignals(False)

    def updateWLMOutput(self, c, signal):
        self.startSwitch.blockSignals(True)
        self.startSwitch.setChecked(signal)
        self.startSwitch.blockSignals(False)

    def updateAmplitude(self, c, signal):
        wmChannel = signal[0]
        value = signal[1]
        if wmChannel in self.d:
            self.d[wmChannel].powermeter.blockSignals(True)
            self.d[wmChannel].powermeter.setValue(value)
            self.d[wmChannel].powermeter.blockSignals(False)

    def updatePattern(self, c, signal):
        chan = signal[0]
        IF1 = signal[1]
        points = 512
        if chan in self.pattern_1:
            self.pattern_1[chan].setData(x=np.arange(points), y=IF1)

    def setButtonOff(self, wmChannel):
        self.d[wmChannel].lockChannel.setChecked(False)

    @inlineCallbacks
    def changeState(self, state, chan):
        yield self.server.set_switcher_signal_state(chan, state)

    @inlineCallbacks
    def lockSingleChannel(self, state, dacPort):
        wmChannel = self.wmChannels[dacPort]
        yield self.server.set_channel_lock(dacPort, wmChannel, state)

    @inlineCallbacks
    def freqChanged(self, freq, dacPort):
        yield self.server.set_pid_course(dacPort, freq)

    @inlineCallbacks
    def setLock(self, state):
        yield self.server.set_lock_state(state)

    @inlineCallbacks
    def setOutput(self, state):
        yield self.server.set_wlm_output(state)

    @inlineCallbacks
    def getPIDCourse(self, dacPort, hint):
        course = yield self.server.get_pid_course(dacPort)
        try:
            course = float(course)
        except:
            try:
                course = float(hint)
            except:
                course = 600
        returnValue(course)

    @inlineCallbacks
    def changeP(self, p, dacPort):
        yield self.server.set_pid_p(dacPort, p)

    @inlineCallbacks
    def changeI(self, i, dacPort):
        yield self.server.set_pid_i(dacPort, i)

    @inlineCallbacks
    def changeD(self, d, dacPort):
        yield self.server.set_pid_d(dacPort, d)

    @inlineCallbacks
    def changeDt(self, dt, dacPort):
        yield self.server.set_pid_dt(dacPort, dt)

    @inlineCallbacks
    def constDt(self, state, dacPort):
        if state == 0:
            yield self.server.set_const_dt(dacPort, False)
        else:
            yield self.server.set_const_dt(dacPort, True)

    @inlineCallbacks
    def changeFactor(self, factor, dacPort):
        yield self.server.set_pid_sensitivity(dacPort, factor, int(self.pid.spinExp.value()))

    @inlineCallbacks
    def changeExponent(self, exponent, dacPort):
        yield self.server.set_pid_sensitivity(dacPort, self.pid.spinFactor.value(), int(exponent))

    @inlineCallbacks
    def changePolarity(self, index, dacPort):
        if index == 0:
            yield self.server.set_pid_polarity(dacPort, 1)
        else:
            yield self.server.set_pid_polarity(dacPort, -1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(multiplexer_client)
