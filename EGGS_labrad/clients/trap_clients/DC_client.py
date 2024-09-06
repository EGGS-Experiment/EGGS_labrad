from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.DC_gui import DC_gui

TOGGLEID =      374683
VOLTAGEID =     374682
HVID =          374861


class DC_client(GUIClient):
    """
    Client for trap DC voltage control via AMO8.
    """

    name = "DC Client"
    servers = {'amo8': 'DC Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = DC_gui('DC Client')
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # try to clear serial buffers upon connection
        try:
            yield self.amo8.serial_flush()
        except Exception as e:
            pass

        # connect to signals
        yield self.amo8.signal__toggle_update(TOGGLEID)
        yield self.amo8.addListener(listener=self.updateToggle, source=None, ID=TOGGLEID)
        yield self.amo8.signal__voltage_update(VOLTAGEID)
        yield self.amo8.addListener(listener=self.updateVoltage, source=None, ID=VOLTAGEID)
        yield self.amo8.signal__hv_update(HVID)
        yield self.amo8.addListener(listener=self.updateHV, source=None, ID=HVID)

        # start device polling
        poll_params = yield self.amo8.polling()
        # only start polling if not started
        if not poll_params[0]:
            # yield self.amo8.polling(True, 5.0)
            pass

    @inlineCallbacks
    def initData(self):
        # get voltages and power states
        voltage_list =  yield self.amo8.voltage_all()
        toggle_list =   yield self.amo8.toggle_all()
        for channel_num, channel_widget in self.gui.amo8_channels.items():
            channel_widget.dac.setValue(voltage_list[channel_num - 1])
            channel_widget.toggleswitch.setChecked(bool(toggle_list[channel_num - 1]))
        # get HV status
        hv_status = yield self.amo8.inputs()
        self.updateHV(None, hv_status)

    def initGUI(self):
        # get endcap numpbers
        endcap_channels =   [channel_params['num']
                            for channel_name, channel_params in self.gui.active_channels.items()
                            if 'ENDCAP' in channel_name.upper()]
        aramp_channels =    [channel_params['num']
                            for channel_name, channel_params in self.gui.active_channels.items()
                            if 'RAMP' in channel_name.upper()]

        # connect global signals
        self.gui.device_global_onswitch.clicked.connect(lambda: self.amo8.toggle_all(True))
        self.gui.device_global_offswitch.clicked.connect(lambda: self.amo8.toggle_all(False))
        self.gui.device_global_clear.clicked.connect(lambda: self.amo8.clear())

        # connect group channel signals
        self.gui.doubleramp_endcaps.clicked.connect(lambda blank: self.startRamp(endcap_channels))
        self.gui.doubleramp_aramp.clicked.connect(lambda blank: self.startRamp(aramp_channels))
        # connect each channel
        for channel in self.gui.amo8_channels.values():
            channel.dac.valueChanged.connect(
                lambda value, _channel_num=channel.number: self.amo8.voltage(_channel_num, value)
            )
            channel.ramp_start.clicked.connect(
                lambda blank, _channel_num=channel.number: self.startRamp([_channel_num])
            )
            channel.toggleswitch.clicked.connect(
                lambda status, _channel_num=channel.number: self.amo8.toggle(_channel_num, status)
            )
            channel.resetswitch.clicked.connect(
                lambda blank, _channel_num=channel.number: self.reset(_channel_num)
            )
            channel.lockswitch.setChecked(False)


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        """
        Resets the given channel.
        Connects to the reset button.
        """
        channel_gui = self.gui.amo8_channels[channel_num]
        # disable GUI
        channel_gui.setEnabled(False)
        channel_gui.blockSignals(True)

        # clear & reset GUI values
        yield self.amo8.voltage(channel_num, 0)
        yield self.amo8.toggle(channel_num, 0)
        channel_gui.dac.setValue(0)
        channel_gui.toggleswitch.setChecked(False)
        channel_gui.ramp_target.setValue(0)
        channel_gui.ramp_rate.setValue(100)

        # reenable GUI
        channel_gui.setEnabled(True)
        channel_gui.blockSignals(False)

    def updateToggle(self, c, signal):
        """
        Toggles the given channel on/off.
        Connects to the on/off button.
        """
        chan_num, status = signal
        if chan_num in self.gui.amo8_channels.keys():
            # set element disable
            widget = self.gui.amo8_channels[chan_num]
            widget.toggleswitch.setEnabled(False)
            widget.toggleswitch.blockSignals(True)
            # update value
            widget.toggleswitch.setChecked(status)
            # enable element
            widget.toggleswitch.setEnabled(True)
            widget.toggleswitch.blockSignals(False)

    def updateVoltage(self, c, signal):
        """
        Updates the voltage of the given channel.
        Connects to the voltage display/DoubleSpinBox.
        """
        chan_num, voltage = signal
        if chan_num in self.gui.amo8_channels.keys():
            widget = self.gui.amo8_channels[chan_num]
            # store lock state & disable updates
            lockstate = widget.lockswitch.isChecked()
            widget.dac.setEnabled(False)
            widget.dac.blockSignals(True)
            # update value & restore previous lockstate
            widget.dac.setValue(voltage)
            widget.dac.setEnabled(lockstate)
            widget.dac.blockSignals(False)

    def updateHV(self, c, hv):
        """
        Updates the High Voltage input monitor.
        Connects to the HV monitor and is triggered by polling.
        """
        self.gui.device_hv_v1.setText(str(hv[0]))   # HV supply current
        self.gui.device_hv_i1.setText(str(hv[1]))   # HV supply voltage

    @inlineCallbacks
    def startRamp(self, channel_list):
        """
        Starts a voltage ramp for a list of channels.
            Yields the ramp request to the device, then blocks user input to the
            ramping channels. _finishRamp is called 3 seconds in the future to
            update the GUI.
        Arguments:
            channel_list    list(int):  a list of channels to ramp.
        """
        # get current values
        end_voltage_list =  []
        rate_list =         []
        for channel_num in channel_list:
            # get current values from channel widget
            channel_gui = self.gui.amo8_channels[channel_num]
            end_voltage_list.append(channel_gui.ramp_target.value())
            rate_list.append(channel_gui.ramp_rate.value())
            # disable channel widget & block from updating
            channel_gui.dac.setEnabled(False)
            channel_gui.dac.blockSignals(True)

        # submit ramp
        yield self.amo8.ramp_multiple(channel_list, end_voltage_list, rate_list)
        # call ramp finish to reenable
        self.reactor.callLater(3, self._finishRamp, channel_list)

    @inlineCallbacks
    def _finishRamp(self, channel_list):
        """
        Finishes the ramp by reenabling the disabled channels.
        Arguments:
            channel_list    list(int):  a list of channels to ramp.
        """
        for channel_num in channel_list:
            voltage_res = yield self.amo8.voltage(channel_num)
            self.gui.amo8_channels[channel_num].dac.setValue(voltage_res)
            self.gui.amo8_channels[channel_num].dac.setEnabled(True)
            self.gui.amo8_channels[channel_num].dac.blockSignals(False)


    # DEPRECATED
    @inlineCallbacks
    def startTriangleRamp(self, channel_list):
        # get current values
        end_voltage_list =  []
        rate_list =         []
        initial_vals =      []
        for channel_num in channel_list:
            channel_gui = self.gui.amo8_channels[channel_num]
            end_voltage_list.append(channel_gui.ramp_target.value())
            rate_list.append(channel_gui.ramp_rate.value())
            initial_vals.append(channel_gui.dac.value())
            # disable GUI from updates/responses
            channel_gui.dac.setEnabled(False)
            channel_gui.ramp_rate.setEnabled(False)
            channel_gui.ramp_target.setEnabled(False)
            channel_gui.blockSignals(True)

        # initiate ramp
        yield self.amo8.ramp_multiple(channel_list, end_voltage_list, rate_list)
        # update GUI after ramp has finished
        self.reactor.callLater(3, self._finishTriangleRamp, channel_list, initial_vals)

    @inlineCallbacks
    def _finishTriangleRamp(self, channel_list, initial_vals):
        # get current values
        for i, channel_num in enumerate(channel_list):
            voltage_res = yield self.amo8.voltage(channel_list)
            channel_gui = self.gui.amo8_channels[channel_num]
            # set new values on GUI & reenable updates/responses
            channel_gui.dac.setValue(voltage_res)
            channel_gui.ramp_target.setValue(initial_vals[i])
            channel_gui.dac.setEnabled(True)
            channel_gui.ramp_rate.setEnabled(True)
            channel_gui.ramp_target.setEnabled(True)
            channel_gui.blockSignals(False)

        # do a startRamp back down
        yield self.startRamp(channel_list)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DC_client)
