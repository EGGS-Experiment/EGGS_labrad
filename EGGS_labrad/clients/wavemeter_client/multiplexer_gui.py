from PyQt5 import QtCore, QtGui, QtWidgets
from EGGS_labrad.clients.Widgets import TextChangingButton as TextChangingButton


class multiplexer_gui(QtWidgets.QFrame):

    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        shell_font = 'MS Shell Dlg 2'
        SLS_gui = self
        SLS_gui.setObjectName("SLS_gui")
        layout = QtWidgets.QGridLayout()

        self.setWindowTitle('Multiplexed wavemeter_client')

        qBox = QtWidgets.QGroupBox('Wave Length and Lock settings')
        subLayout = QtWidgets.QGridLayout()
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