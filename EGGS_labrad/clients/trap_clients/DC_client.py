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
        self.gui.doubleramp_endcaps.clicked.connect(lambda blank: self.doubleramp(1, 2))
        #self.gui.doublechange_endcaps.clicked.connect(lambda blank: self.doublechange(1, 2))
        self.gui.doubleramp_aramp.clicked.connect(lambda blank: self.doubleramp(5, 6))
        #self.gui.doublechange_aramp.clicked.connect(lambda blank: self.doublechange(5, 6))
        # todo: stop using self.gui.amo8_channels and move config to client side
        # connect each channel
        for channel in self.gui.amo8_channels.values():
            channel.dac.valueChanged.connect(lambda value, _channel_num=channel.number: self.amo8.voltage(_channel_num, value))
            channel.ramp_start.clicked.connect(lambda blank, _channel_num=channel.number: self.startRamp(_channel_num))
            channel.toggleswitch.clicked.connect(lambda status, _channel_num=channel.number:
                                                 self.amo8.toggle(_channel_num, status))
            channel.resetswitch.clicked.connect(lambda blank, _channel_num=channel.number: self.reset(_channel_num))


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        yield self.amo8.voltage(channel_num, 0)
        yield self.amo8.toggle(channel_num, 0)

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
            widget.dac.setEnabled(False)
            # update value
            widget.dac.setValue(voltage)
            # enable element
            widget.dac.setEnabled(True)

    def updateHV(self, c, hv):
        self.gui.device_hv_v1.setText(str(hv[0]))
        self.gui.device_hv_i1.setText(str(hv[1]))

    @inlineCallbacks
    def startRamp(self, chan_num):
        channel = self.gui.amo8_channels[chan_num]
        end_voltage = channel.ramp_target.value()
        rate = channel.ramp_rate.value()
        channel.dac.setEnabled(False)
        yield self.amo8.ramp(chan_num, end_voltage, rate)
        self.reactor.callLater(3, self.finishRamp, [chan_num])

    @inlineCallbacks
    def finishRamp(self, chan_nums):
        for chan_num in chan_nums:
            voltage_res = yield self.amo8.voltage(chan_num)
            self.gui.amo8_channels[chan_num].dac.setEnabled(True)
            self.gui.amo8_channels[chan_num].dac.setValue(voltage_res)


    # todo: tmp remove
    @inlineCallbacks
    def doubleramp(self, chan1, chan2):
        # get current values
        channel1 = self.gui.amo8_channels[chan1]
        channel2 = self.gui.amo8_channels[chan2]
        end_voltage1 = channel1.ramp_target.value()
        rate1 = channel1.ramp_rate.value()
        end_voltage2 = channel2.ramp_target.value()
        rate2 = channel2.ramp_rate.value()
        channel1.dac.setEnabled(False)
        channel2.dac.setEnabled(False)
        print([chan1, chan2], [end_voltage1, end_voltage2], [rate1, rate2])
        yield self.amo8.ramp_multiple([chan1, chan2], [end_voltage1, end_voltage2], [rate1, rate2])
        self.reactor.callLater(3, self.finishRamp, [chan1, chan2])


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DC_client)
