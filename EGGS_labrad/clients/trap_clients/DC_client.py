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
        # connect each channel
        for channel in self.gui.amo8_channels.values():
            channel.dac.valueChanged.connect(lambda value, _channel_num=channel.number: self.amo8.voltage(_channel_num, value))
            #channel.ramp_start.clicked.connect(lambda voltage=channel.ramp_target.value(), rate=channel.ramp_rate.value():
                                               #self.amo8.ramp(channel.number, voltage, rate))
            channel.toggleswitch.clicked.connect(lambda status=channel.lockswitch.isChecked(), _channel_num=channel.number:
                                           self.amo8.toggle(_channel_num, status))
            channel.resetswitch.clicked.connect(lambda: self.reset(channel.number))


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
        from time import sleep
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


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DC_client)
