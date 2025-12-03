from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.toptica_client.toptica_gui import toptica_gui
import traceback

# used for default GUI loading in case of error
TOPTICA_CHANNELS = [(1, 'DLpro (S/N 029432)', '397'),
                    (2, 'DLpro (S/N 022111)', '852.36'),
                    (3, 'DLpro (S/N 029431)', '422'),
                    (4, 'DLpro (S/N 021957)', '850')]

# IDs for actual values being outputted by toptica device
CURRENTACTUALUPDATED_ID = 192611
TEMPERATUREACTUALUPDATED_ID = 192612
PIEZOACTUALUPDATED_ID = 192613

# IDs for values set by user
CURRENTSETUPDATED_ID = 192614
TEMPERATURESETUPDATED_ID = 192615
PIEZOSETUPDATED_ID = 192616

# IDs for max values set by user
CURRENTMAXUPDATED_ID = 192617

# ID for enabled status of toptica device
TOGGLEUPDATED_ID = 192620

# useful for string parsing
DEVICE_TYPE_PREFIX = {
    'DLpro':        'dl',
    'BoosTApro':    'amp',
}

# determine which devices have a piezo to control
DEVICES_USE_PIEZO = {
    'DLpro': True,
    'BoosTApro': False,
}

class toptica_client(GUIClient):

    name = 'Toptica Client'
    servers = {'toptica': 'toptica_server'}

    def getgui(self):
        if self.gui is None:
            self.gui = toptica_gui(TOPTICA_CHANNELS)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # get config
        self.channelinfo = yield self.toptica.device_list()
        # connect to device signals
        yield self.toptica.signal__current_actual_updated(CURRENTACTUALUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateCurrentActual, source=None, ID=CURRENTACTUALUPDATED_ID)
        yield self.toptica.signal__temperature_actual_updated(TEMPERATUREACTUALUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateTemperatureActual, source=None, ID=TEMPERATUREACTUALUPDATED_ID)
        yield self.toptica.signal__piezo_actual_updated(PIEZOACTUALUPDATED_ID)
        yield self.toptica.addListener(listener=self.updatePiezoActual, source=None, ID=PIEZOACTUALUPDATED_ID)
        # connect to user-set parameters
        yield self.toptica.signal__current_set_updated(CURRENTSETUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateCurrentSet, source=None, ID=CURRENTSETUPDATED_ID)
        yield self.toptica.signal__temperature_set_updated(TEMPERATURESETUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateTemperatureSet, source=None, ID=TEMPERATURESETUPDATED_ID)
        yield self.toptica.signal__piezo_set_updated(PIEZOSETUPDATED_ID)
        yield self.toptica.addListener(listener=self.updatePiezoSet, source=None, ID=PIEZOSETUPDATED_ID)
        # connect to user-set max parameters
        yield self.toptica.signal__current_max_updated(CURRENTMAXUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateCurrentMax, source=None, ID=CURRENTMAXUPDATED_ID)
        # connet to enabled status of toptica device
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

                # todo: process device info more programmatically in case different results
                # todo: really important we handle things correctly, otherwise might fuck things up
                device_info_dict = dict(device_info)
                name = device_info_dict.get('name', None)
                wav = device_info_dict.get('wavelength', None)
                dev_type = device_info_dict.get('type', None)
                # _, name, _, wav, _, _, _, _ = device_info

                # determine if toptica device is enabled
                enabled_status = yield self.toptica.toggle(chan_num)
                widget.statusBox.channelDisplay.setText(str(chan_num))
                name_tmp = name.split('S/N ')[1]
                name_tmp = name_tmp[:-1]
                widget.statusBox.serDisplay.setText(name_tmp)
                widget.statusBox.wavDisplay.setText(wav)
                widget.statusBox.enabledButton.setChecked(enabled_status)

                # feedback
                # todo

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
                temperature_min = yield self.toptica.temperature_min(chan_num)
                temperature_max = yield self.toptica.temperature_max(chan_num)
                temperature_actual = yield self.toptica.temperature_actual(chan_num)
                widget.tempBox.setBox.setValue(temperature_set)
                widget.tempBox.minBox.setText('{:0.4f}'.format(temperature_min))
                widget.tempBox.maxBox.setText('{:0.4f}'.format(temperature_max))
                widget.tempBox.actualValue.setText('{:0.4f}'.format(temperature_actual))
                widget.tempBox.lockswitch.setChecked(False)

                # piezo
                if DEVICES_USE_PIEZO[dev_type]:
                    piezo_set = yield self.toptica.piezo_set(chan_num)
                    piezo_min = yield self.toptica.piezo_min(chan_num)
                    piezo_max = yield self.toptica.piezo_max(chan_num)
                    piezo_actual = yield self.toptica.piezo_actual(chan_num)
                    widget.piezoBox.setBox.setValue(piezo_set)
                    widget.piezoBox.minBox.setText('{:0.4f}'.format(piezo_min))
                    widget.piezoBox.maxBox.setText('{:0.4f}'.format(piezo_max))
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
            #todo: set enabled button, assign feedback slots, assign current slots

            # assign enabled slot
            widget.statusBox.enabledButton.clicked.connect(lambda value, _chan_num=chan_num: self.toptica.toggle(_chan_num, value))
            # # assign current slots (only update device once RETURN key is pressed)
            widget.currBox.setBox.textChanged.connect(lambda _: widget.currBox.setBox.blockSignals(True))
            widget.currBox.setBox.lineEdit().returnPressed.connect(lambda _chan_num=chan_num,
                                                                          _box= widget.currBox.setBox,
                                                                          _device_func = self.toptica.current_set:
                                                       self.updateVal(None, _box, _chan_num, _device_func))
            widget.currBox.maxBox.textChanged.connect(lambda _: widget.currBox.maxBox.blockSignals(True))
            widget.currBox.maxBox.lineEdit().returnPressed.connect(lambda _chan_num=chan_num,
                                                                          _box=widget.currBox.maxBox,
                                                                          _device_func = self.toptica.current_max:
                                                          self.updateVal(None, _box, _chan_num, _device_func))
            # assign temperature slots (only update device once RETURN key is pressed)
            widget.tempBox.setBox.textChanged.connect(lambda _: widget.tempBox.setBox.blockSignals(True))
            widget.tempBox.setBox.lineEdit().returnPressed.connect(lambda _chan_num=chan_num,
                                                                          _box=widget.tempBox.setBox,
                                                                          _device_func =self.toptica.temperature_set:
                                                            self.updateVal(None, _box, _chan_num, _device_func))
            # assign piezo slots (only update device once RETURN key is pressed)
            if widget.piezo:
                widget.piezoBox.setBox.textChanged.connect(lambda _: widget.piezoBox.setBox.blockSignals(True))
                widget.piezoBox.setBox.lineEdit().returnPressed.connect(lambda _chan_num=chan_num,
                                                                               _box=widget.piezoBox.setBox,
                                                                               _device_func=self.toptica.piezo_set:
                                                            self.updateVal(None, _box, _chan_num, _device_func))
            # assign scan slots
            #widget.scanBox.modeBox.currentItemChanged.connect(lambda index, _chan_num=chan_num: self.toptica.scan_mode(_chan_num, index))
            #widget.scanBox.shapeBox.currentItemChanged.connect(lambda index, _chan_num=chan_num: self.toptica.scan_shape(_chan_num, index))
            widget.scanBox.freqBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_frequency(_chan_num, value))
            widget.scanBox.ampBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_amplitude(_chan_num, value))
            widget.scanBox.offBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_offset(_chan_num, value))

    # SIGNALS
    def updateVal(self, c, box, chan_num,device_func):
        """
        Update the toptica device based on input to the gui
        Args:
            c: labrad context
            box: gui element to read from
            chan_num: numvber of channel used to talk to toptica device
            device_func: function to talk to toptica device/controller
        """
        val = float(box.text())
        box.blockSignals(False)
        device_func(chan_num, val)

    # SLOTS
    def updateCurrentActual(self, c, signal):
        """
        Update the listed actual current based on information from the toptica controller
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, curr = signal
        box = self.gui.channels[chan_num].currBox.actualValue
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setText('{:0.4f}'.format(curr))
            box.blockSignals(False)

    def updateTemperatureActual(self, c, signal):
        """
        Update the actual temperature of the toptica device based on information from its controller
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, temp = signal
        box = self.gui.channels[chan_num].tempBox.actualValue
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setText('{:0.4f}'.format(temp))
            box.blockSignals(False)

    def updatePiezoActual(self, c, signal):
        """
        Update the actual piezo voltage listed based information from the toptica box
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, voltage = signal
        box = self.gui.channels[chan_num].piezoBox.actualValue
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setText('{:0.4f}'.format(voltage))
            box.blockSignals(False)

    def updateCurrentSet(self, c, signal):
        """
        Update the set current listed based on the actions of other clients
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, curr = signal
        box = self.gui.channels[chan_num].currBox.setBox
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setValue(curr)
            box.blockSignals(False)

    def updateTemperatureSet(self, c, signal):
        chan_num, temp = signal
        box = self.gui.channels[chan_num].tempBox.setBox
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setValue(temp)
            box.blockSignals(False)

    def updatePiezoSet(self, c, signal):
        """
        Update the set voltage listed for the piezo based on the actions of other clients
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, voltage = signal
        box = self.gui.channels[chan_num].piezoBox.setBox
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setValue(voltage)
            box.blockSignals(False)

    def updateCurrentMax(self, c, signal):
        """
        Update the max current listed based on the actions of other clients
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, curr = signal
        box = self.gui.channels[chan_num].currBox.maxBox
        if chan_num in self.gui.channels.keys() and not box.signalsBlocked():
            box.blockSignals(True)
            box.setValue(curr)
            box.blockSignals(False)

    def updateEnabledButton(self, c, signal):
        """
        Change the status of the enabled button based on the actions of other clients
        Args:
            c: labrad context
            signal: event result to process
        """
        chan_num, status = signal
        button = self.gui.channels[chan_num].statusBox.enabledButton
        if chan_num in self.gui.channels.keys() and not button.signalsBlocked():
            button.blockSignals(True)
            button.setChecked(status)
            button.setAppearance(status)
            button.blockSignals(False)

if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(toptica_client)
