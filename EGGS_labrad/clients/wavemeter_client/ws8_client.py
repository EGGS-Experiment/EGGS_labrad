from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.DC_gui import DC_gui

from common.lib.clients.qtui.multiplexerchannel_no_pid import QCustomWavemeterChannel
from common.lib.clients.qtui.q_custom_text_changing_button import \
    TextChangingButton

from pyqtgraph.Qt import QtGui

from twisted.internet.defer import inlineCallbacks
try:
    from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
except:
    pass

import socket
import os

SIGNALID1 = 445566
SIGNALID2 = 143533
SIGNALID3 = 111221
SIGNALID4 = 549210
SIGNALID5 = 190909
SIGNALID6 = 102588
SIGNALID7 = 148323
SIGNALID8 = 238883


class wavemeterclient(QtGui.QWidget):

    def __init__(self, reactor, parent=None):
        """initializes the GUI, creates the reactor
            and empty dictionary for channel widgets to
            be stored for iteration. also grabs chan info
            from multiplexer_config
        """
        super(wavemeterclient, self).__init__()
        self.password = os.environ['LABRADPASSWORD']
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.name = socket.gethostname() + ' Wave Meter Client'
        self.d = {}
        self.wmChannels = {}
        self.connect()
        self._check_window_size()


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
        yield self.server.signal__output_changed(SIGNALID5)
        yield self.server.signal__amplitude_changed(SIGNALID8)

        yield self.server.addListener(listener=self.updateFrequency, source=None, ID=SIGNALID1)
        yield self.server.addListener(listener=self.toggleMeas, source=None, ID=SIGNALID2)
        yield self.server.addListener(listener=self.updateexp, source=None, ID=SIGNALID3)
        yield self.server.addListener(listener=self.updateWLMOutput, source=None, ID=SIGNALID5)
        yield self.server.addListener(listener=self.updateAmplitude, source=None, ID=SIGNALID8)

        # starts display of wavemeter data
        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):
        layout = QtGui.QGridLayout()

        self.setWindowTitle('Wavemeter')

        # this "group" contains all 8 channel outputs and settings
        qBox = QtGui.QGroupBox('Wave Length and Lock settings')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        # button to start wavemeter measurement (turn wavemeter on)
        self.startSwitch = TextChangingButton('Wavemeter')
        self.startSwitch.setMaximumHeight(50)
        initstartvalue = yield self.server.get_wlm_output()
        self.startSwitch.setChecked(initstartvalue)
        self.startSwitch.toggled.connect(self.setOutput)
        subLayout.addWidget(self.startSwitch, 0, 0)

        # create display box for each channel
        # need to modify QCustomWavemeterChannel to get rid of PID button
        for chan in self.chaninfo:
            wmChannel = self.chaninfo[chan][0]
            hint = self.chaninfo[chan][1]
            position = self.chaninfo[chan][2]
            stretched = self.chaninfo[chan][3]
            widget = QCustomWavemeterChannel(chan, wmChannel, hint, stretched)

            from common.lib.clients.qtui import RGBconverter as RGB
            RGB = RGB.RGBconverter()
            color = int(2.998e8/(float(hint)*1e3))
            color = RGB.wav2RGB(color)
            color = tuple(color)

            widget.currentfrequency.setStyleSheet('color: rgb' + str(color))
            widget.spinExp.valueChanged.connect(lambda exp=widget.spinExp.value(), wmChannel=wmChannel : self.expChanged(exp, wmChannel))
            initvalue = yield self.server.get_exposure(wmChannel)
            widget.spinExp.setValue(initvalue)
            initmeas = yield self.server.get_switcher_signal_state(wmChannel)
            initmeas = initmeas
            widget.measSwitch.setChecked(bool(initmeas))
            widget.measSwitch.toggled.connect(lambda state=widget.measSwitch.isDown(), wmChannel=wmChannel  : self.changeState(state, wmChannel))

            self.d[wmChannel] = widget
            subLayout.addWidget(self.d[wmChannel], position[1], position[0], 1, 3)

        self.setLayout(layout)

    # updates exposure time from GUI?
    @inlineCallbacks
    def expChanged(self, exp, chan):
        # these are switched, dont know why
        exp = int(exp)
        yield self.server.set_exposure_time(chan, exp)

    # sets display of update frequency and light exposure level
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

    def toggleMeas(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].measSwitch.setChecked(value)

    def updateexp(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].spinExp.setValue(value)

    def updateWLMOutput(self, c, signal):
        self.startSwitch.setChecked(signal)

    def updateAmplitude(self, c, signal):
        wmChannel = signal[0]
        value = signal[1]
        if wmChannel in self.d:
            self.d[wmChannel].powermeter.setValue(value)

    def setButtonOff(self, wmChannel):
        self.d[wmChannel].lockChannel.setChecked(False)

    @inlineCallbacks
    def changeState(self, state, chan):
        yield self.server.set_switcher_signal_state(chan, state)

    @inlineCallbacks
    def setOutput(self, state):
        yield self.server.set_wlm_output(state)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(wavemeterclient)
