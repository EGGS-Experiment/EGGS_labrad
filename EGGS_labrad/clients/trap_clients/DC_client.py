from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.DC_gui import DC_gui


class DC_client(GUIClient):
    """
    Client for DC voltage control via AMO8.
    """

    name = "DC Client"
    HVID = 374861
    servers = {'amo8': 'DC Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = DC_gui('DC Client')
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to signals
        yield self.amo8.signal__hv_update(self.HVID)
        yield self.amo8.addListener(listener=self.updateHV, source=None, ID=self.HVID)

    @inlineCallbacks
    def initData(self):
        v1 = yield self.amo8.voltage(1)
        v2 = yield self.amo8.voltage(2)
        v3 = yield self.amo8.voltage(3)
        v4 = yield self.amo8.voltage(4)
        v_list = [v1, v2, v3, v4]
        for i in range(len(self.gui.amo8_channels)):
            self.gui.amo8_channels[i].dac.setValue(v_list[i])
            self.gui.amo8_channels[i].toggleswitch.setChecked(v_list[i])
        """
        voltage_list = yield self.amo8.voltage(-1)
        voltage_list = [voltage_list[channel.number] for channel in self.gui.amo8_channels]
        toggle_list = yield self.amo8.toggle(-1)
        toggle_list = [toggle_list[channel.number] for channel in self.gui.amo8_channels]
        for i in range(len(self.amo8_channels)):
            self.gui.amo8_channels[i].dac.setValue(voltage_list[i])
            self.gui.amo8_channels[i].toggle.setChecked(toggle_list[i])
        """

    def initGUI(self):
        # connect global signals
        #self.gui.device_global_onswitch.clicked.connect(lambda: self.amo8.toggle(-1, 1))
        #self.gui.device_global_offswitch.clicked.connect(lambda: self.amo8.toggle(-1, 0))
        #self.gui.device_global_clear.clicked.connect(lambda: self.amo8.clear())
        # connect each channel
        for channel in self.gui.amo8_channels:
            channel.dac.valueChanged.connect(lambda value, _channel_num=channel.number: self.amo8.voltage(_channel_num, value))
            #channel.ramp_start.clicked.connect(lambda voltage=channel.ramp_target.value(), rate=channel.ramp_rate.value():
                                               #self.amo8.ramp(channel.number, voltage, rate))
            channel.toggleswitch.clicked.connect(lambda status=channel.lockswitch.isChecked(), _channel_num=channel.number:
                                           self.amo8.toggle(_channel_num, status))
            #channel.resetswitch.clicked.connect(lambda: self.reset(channel.number))


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        yield self.amo8.voltage(channel_num, 0)
        yield self.amo8.toggle(channel_num, 0)

    def updateHV(self, hv):
        self.gui.device_hv_monitor.device_hv_v1.setText(str(hv[0]))
        self.gui.device_hv_monitor.device_hv_i1.setText(str(hv[1]))


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DC_client)
