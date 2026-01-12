from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.toptica_client.toptica_gui import toptica_gui

import traceback

# used for default GUI loading in case of error
TOPTICA_CHANNELS = [
    (1, 'DLpro (S/N 029432)', 'DLpro', '397'),
    (2, 'DLpro (S/N 022111)', 'DLpro', '852.36'),
    (3, 'DLpro (S/N 029431)', 'DLpro', '422'),
    (4, 'DLpro (S/N 021957)', 'DLpro', '850')
]

# IDs for actual values being outputted by toptica device
PARAMETER_ACTUAL_ID =   193611
PARAMETER_SET_ID =      193612
TOGGLEUPDATED_ID =      192620

# useful for string parsing
DEVICE_TYPE_PREFIX = {
    'DLpro':        'dl',
    'BoosTApro':    'amp',
}

# determine which devices have a piezo to control
DEVICES_USE_PIEZO = {
    'DLpro':        True,
    'BoosTApro':    False,
}

# todo: make check signalsBlocked before polling etc can update


class toptica_client(GUIClient):

    name = 'Toptica Client'
    servers = {'toptica': 'toptica_server'}

    def getgui(self):
        if self.gui is None:
            self.gui = toptica_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # get device config
        self.channelinfo = yield self.toptica.device_list()

        # connect to device signals
        yield self.toptica.signal__parameter_actual(PARAMETER_ACTUAL_ID)
        yield self.toptica.addListener(listener=self.updateParameterActual, source=None, ID=PARAMETER_ACTUAL_ID)
        yield self.toptica.signal__parameter_set(PARAMETER_SET_ID)
        yield self.toptica.addListener(listener=self.updateParameterSet, source=None, ID=PARAMETER_SET_ID)
        yield self.toptica.signal__toggle_updated(TOGGLEUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateEnabledButton, source=None, ID=TOGGLEUPDATED_ID)

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # start device polling if not already started
        poll_params = yield self.toptica.polling()
        if not poll_params[0]:
            yield self.toptica.polling(True, 10.0)

    @inlineCallbacks
    def initData(self):
        try:
            self.gui.makeLayout(self.channelinfo)
            self.gui.show()

            # set display for each channel
            for chan_num, widget in self.gui.channels.items():
                # status
                device_info = yield self.toptica.device_info(chan_num)
                device_info_dict = dict(device_info)
                name = device_info_dict.get('name', None)
                wav = device_info_dict.get('wavelength', None)
                dev_type = device_info_dict.get('type', None)

                # determine if toptica device is enabled
                enabled_status = yield self.toptica.toggle(chan_num)
                widget.statusBox.channelDisplay.setText(str(chan_num))
                widget.statusBox.serDisplay.setText(name.split('S/N ')[1][:-1])
                widget.statusBox.wavDisplay.setText(wav)
                widget.statusBox.enabledButton.setChecked(enabled_status)

                # current
                current_set = yield self.toptica.current_set(chan_num)
                current_max = yield self.toptica.current_max(chan_num)
                current_actual = yield self.toptica.current_actual(chan_num)
                widget.currBox.setBox.setValue(current_set)
                widget.currBox.maxBox.setValue(current_max)
                widget.currBox.actualValue.setText('{:0.4f}'.format(current_actual))
                widget.currBox.lockswitch.setChecked(False)

                # temperature
                temperature_set = yield self.toptica.temperature_set(chan_num)
                temperature_actual = yield self.toptica.temperature_actual(chan_num)
                widget.tempBox.setBox.setValue(temperature_set)
                widget.tempBox.minBox.setText('{:0.4f}'.format(float(device_info_dict["temp_min"])))
                widget.tempBox.maxBox.setText('{:0.4f}'.format(float(device_info_dict["temp_max"])))
                widget.tempBox.actualValue.setText('{:0.4f}'.format(temperature_actual))
                widget.tempBox.lockswitch.setChecked(False)

                # piezo
                if DEVICES_USE_PIEZO[dev_type]:
                    piezo_set = yield self.toptica.piezo_set(chan_num)
                    piezo_actual = yield self.toptica.piezo_actual(chan_num)
                    widget.piezoBox.setBox.setValue(piezo_set)
                    widget.piezoBox.minBox.setText('{:0.4f}'.format(float(device_info_dict["piezo_min"])))
                    widget.piezoBox.maxBox.setText('{:0.4f}'.format(float(device_info_dict["piezo_max"])))
                    widget.piezoBox.actualValue.setText('{:0.4f}'.format(piezo_actual))
                    widget.piezoBox.lockswitch.setChecked(False)

                # scan
                scan_freq = yield self.toptica.scan_frequency(chan_num)
                scan_amp = yield self.toptica.scan_amplitude(chan_num)
                scan_off = yield self.toptica.scan_offset(chan_num)
                widget.scanBox.freqBox.setValue(scan_freq)
                widget.scanBox.ampBox.setValue(scan_amp)
                widget.scanBox.offBox.setValue(scan_off)
                widget.scanBox.lockswitch.setChecked(False)

        except Exception as e:
            print('\n\tERROR!\n')
            print(traceback.format_exc())
            raise e

    def initGUI(self):
        # laser channel settings
        for chan_num, widget in self.gui.channels.items():
            # assign enabled slot
            widget.statusBox.enabledButton.clicked.connect(lambda value, _chan_num=chan_num: self.toptica.toggle(_chan_num, value))

            # # assign current slots (only update device once RETURN key is pressed)
            widget.currBox.setBox.textChanged.connect(lambda _: widget.currBox.setBox.blockSignals(True))
            widget.currBox.setBox.lineEdit().returnPressed.connect(
                lambda _chan_num=chan_num, _box=widget.currBox.setBox, _device_func=self.toptica.current_set:
                self.updateVal(_box, _chan_num, _device_func))

            widget.currBox.maxBox.textChanged.connect(lambda _: widget.currBox.maxBox.blockSignals(True))
            widget.currBox.maxBox.lineEdit().returnPressed.connect(
                lambda _chan_num=chan_num, _box=widget.currBox.maxBox, _device_func=self.toptica.current_max:
                self.updateVal(_box, _chan_num, _device_func))

            # assign temperature slots (only update device once RETURN key is pressed)
            widget.tempBox.setBox.textChanged.connect(lambda _: widget.tempBox.setBox.blockSignals(True))
            widget.tempBox.setBox.lineEdit().returnPressed.connect(
                lambda _chan_num=chan_num, _box=widget.tempBox.setBox, _device_func=self.toptica.temperature_set:
                self.updateVal(_box, _chan_num, _device_func))

            # assign piezo slots (only update device once RETURN key is pressed)
            if DEVICES_USE_PIEZO[widget.dev_type]:
                widget.piezoBox.setBox.textChanged.connect(lambda _: widget.piezoBox.setBox.blockSignals(True))
                widget.piezoBox.setBox.lineEdit().returnPressed.connect(
                    lambda _chan_num=chan_num, _box=widget.piezoBox.setBox, _device_func=self.toptica.piezo_set:
                    self.updateVal(_box, _chan_num, _device_func))

            # assign scan slots
            widget.scanBox.freqBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_frequency(_chan_num, value))
            widget.scanBox.ampBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_amplitude(_chan_num, value))
            widget.scanBox.offBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_offset(_chan_num, value))


    """
    SIGNALS
    """
    def updateVal(self, box, chan_num, device_func):
        """
        Update the toptica device based on input to the gui
        Args:
            c: labrad context
            box: gui element to read from
            chan_num: numvber of channel used to talk to toptica device
            device_func: function to talk to toptica device/controller
        """
        val = float(box.text())
        box.blockSignals(True)
        device_func(chan_num, val)
        box.blockSignals(False)


    """
    SLOTS
    """
    def updateParameterActual(self, c, signal):
        """
        Update the parameter reading based on information from the toptica controller
        Args:
            c: labrad context
            signal: event result to process
        """
        # assign signal to target
        param_name, chan_num, param_val = signal
        if chan_num in self.gui.channels.keys():
            if param_name == "current-act":
                box = self.gui.channels[chan_num].currBox.actualValue
            elif param_name == "temp-act":
                box = self.gui.channels[chan_num].tempBox.actualValue
            elif param_name == "voltage-act":
                box = self.gui.channels[chan_num].piezoBox.actualValue
        else:   return

        # update GUI
        if not box.signalsBlocked():
            box.blockSignals(True)
            box.setText('{:0.3f}'.format(param_val))
            box.blockSignals(False)

    def updateParameterSet(self, c, signal):
        """
        Update the parameter setting based on information from the toptica controller
        Args:
            c: labrad context
            signal: event result to process
        """
        # assign signal to target
        param_name, chan_num, param_val = signal
        if chan_num in self.gui.channels.keys():
            if param_name == "current-set":
                box = self.gui.channels[chan_num].currBox.setBox
            elif param_name == "temp-set":
                box = self.gui.channels[chan_num].tempBox.setBox
            elif param_name == "voltage-set":
                box = self.gui.channels[chan_num].piezoBox.setBox
            elif param_name == "current-clip":
                box = self.gui.channels[chan_num].currBox.maxBox
        else:   return

        # update GUI
        if not box.signalsBlocked() and not box.hasFocus():
            box.blockSignals(True)
            box.setValue(param_val)
            box.blockSignals(False)

    def updateEnabledButton(self, c, signal):
        """
        Change the status of the enabled button based on the actions of other clients
        Args:
            c: labrad context
            signal: event result to process
        """
        # assign signal to target
        chan_num, status = signal
        if chan_num in self.gui.channels.keys():
            button = self.gui.channels[chan_num].statusBox.enabledButton
        else:   return

        if not button.signalsBlocked() and not button.hasFocus():
            button.blockSignals(True)
            button.setChecked(status)
            button.setAppearance(status)
            button.blockSignals(False)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(toptica_client)
