from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.DC_gui import DC_gui

TOGGLEID = 374683
VOLTAGEID = 374682
HVID = 374861


class DC_client(GUIClient):
    """
    Client for DC voltage control via AMO8.
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
        # todo: get config from registry
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
            yield self.amo8.polling(True, 5.0)

    @inlineCallbacks
    def initData(self):
        # get voltages and power states
        voltage_list = yield self.amo8.voltage_all()
        toggle_list = yield self.amo8.toggle_all()
        for channel_num, channel_widget in self.gui.amo8_channels.items():
            channel_widget.dac.setValue(voltage_list[channel_num - 1])
            channel_widget.toggleswitch.setChecked(bool(toggle_list[channel_num - 1]))
        # get HV status
        hv_status = yield self.amo8.inputs()
        self.updateHV(None, hv_status)

    def initGUI(self):
        # connect global signals
        self.gui.device_global_onswitch.clicked.connect(lambda: self.amo8.toggle_all(True))
        self.gui.device_global_offswitch.clicked.connect(lambda: self.amo8.toggle_all(False))
        self.gui.device_global_clear.clicked.connect(lambda: self.amo8.clear())
        self.gui.doubleramp_endcaps.clicked.connect(lambda blank: self.startRamp([1, 2]))
        self.gui.doubleramp_aramp.clicked.connect(lambda blank: self.startRamp([5, 6]))
        self.gui.triangleramp_aramp.clicked.connect(lambda blank: self.startTriangleRamp([5, 6]))
        #self.gui.doublechange_endcaps.clicked.connect(lambda blank: self.doublechange(1, 2))
        #self.gui.doublechange_aramp.clicked.connect(lambda blank: self.doublechange(5, 6))
        # todo: stop using self.gui.amo8_channels and move config to client side
        # connect each channel
        for channel in self.gui.amo8_channels.values():
            channel.dac.valueChanged.connect(lambda value, _channel_num=channel.number: self.amo8.voltage(_channel_num, value))
            channel.ramp_start.clicked.connect(lambda blank, _channel_num=channel.number: self.startRamp([_channel_num]))
            channel.toggleswitch.clicked.connect(lambda status, _channel_num=channel.number:
                                                 self.amo8.toggle(_channel_num, status))
            channel.resetswitch.clicked.connect(lambda blank, _channel_num=channel.number: self.reset(_channel_num))
            channel.lockswitch.setChecked(False)


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        channel_gui = self.gui.amo8_channels[channel_num]
        channel_gui.setEnabled(False)
        yield self.amo8.voltage(channel_num, 0)
        yield self.amo8.toggle(channel_num, 0)
        channel_gui.dac.setValue(0)
        channel_gui.toggleswitch.setChecked(False)
        channel_gui.ramp_target.setValue(0)
        channel_gui.ramp_rate.setValue(0)
        channel_gui.setEnabled(True)

    def updateToggle(self, c, signal):
        chan_num, status = signal
        if chan_num in self.gui.amo8_channels.keys():
            # set element disable
            widget = self.gui.amo8_channels[chan_num]
            widget.toggleswitch.setEnabled(False)
            # update value
            widget.toggleswitch.setChecked(status)
            # enable element
            widget.toggleswitch.setEnabled(True)

    def updateVoltage(self, c, signal):
        chan_num, voltage = signal
        if chan_num in self.gui.amo8_channels.keys():
            # set element disable
            widget = self.gui.amo8_channels[chan_num]
            # store lock state
            lockstate = widget.lockswitch.isChecked()
            widget.dac.setEnabled(False)
            # update value
            widget.dac.setValue(voltage)
            # restore previous lockstate
            widget.dac.setEnabled(lockstate)

    def updateHV(self, c, hv):
        self.gui.device_hv_v1.setText(str(hv[0]))
        self.gui.device_hv_i1.setText(str(hv[1]))

    @inlineCallbacks
    def startTriangleRamp(self, channel_list):
        # get current values
        end_voltage_list = []
        rate_list = []
        initial_vals = []
        for channel_num in channel_list:
            channel_gui = self.gui.amo8_channels[channel_num]
            end_voltage_list.append(channel_gui.ramp_target.value())
            rate_list.append(channel_gui.ramp_rate.value())
            initial_vals.append(channel_gui.dac.value())
            channel_gui.dac.setEnabled(False)
            channel_gui.ramp_rate.setEnabled(False)
            channel_gui.ramp_target.setEnabled(False)
        print('initial vals:', initial_vals)
        yield self.amo8.ramp_multiple(channel_list, end_voltage_list, rate_list)
        self.reactor.callLater(3, self.finishTriangleRamp, channel_list, initial_vals)

    @inlineCallbacks
    def finishTriangleRamp(self, channel_list, initial_vals):
        # get value
        for i, channel_num in enumerate(channel_list):
            voltage_res = yield self.amo8.voltage(channel_list)
            channel_gui = self.gui.amo8_channels[channel_num]
            channel_gui.dac.setValue(voltage_res)
            channel_gui.dac.setEnabled(True)
            channel_gui.ramp_rate.setEnabled(True)
            channel_gui.ramp_target.setEnabled(True)
            channel_gui.ramp_target.setValue(initial_vals[i])
        # do a startRamp back down
        yield self.startRamp(channel_list)

    @inlineCallbacks
    def startRamp(self, channel_list):
        # get current values
        end_voltage_list = []
        rate_list = []
        for channel_num in channel_list:
            channel_gui = self.gui.amo8_channels[channel_num]
            end_voltage_list.append(channel_gui.ramp_target.value())
            rate_list.append(channel_gui.ramp_rate.value())
            channel_gui.dac.setEnabled(False)
        yield self.amo8.ramp_multiple(channel_list, end_voltage_list, rate_list)
        self.reactor.callLater(3, self.finishRamp, channel_list)

    @inlineCallbacks
    def finishRamp(self, channel_list):
        for channel_num in channel_list:
            voltage_res = yield self.amo8.voltage(channel_num)
            self.gui.amo8_channels[channel_num].dac.setValue(voltage_res)
            self.gui.amo8_channels[channel_num].dac.setEnabled(True)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DC_client)
