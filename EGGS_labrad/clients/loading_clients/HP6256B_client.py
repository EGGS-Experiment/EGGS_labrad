from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.loading_clients.HP6256B_gui import HP6256B_gui


class HP6256B_client(GUIClient):
    """
    Client for HP6256B control via ARTIQ.
    """

    name = "HP6256B Client"
    HVID = 374861
    servers = {'hp': 'HP6256B Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = HP6256B_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to signals
        yield self.hp.signal__hv_update(self.HVID)
        yield self.hp.addListener(listener=self.updateHV, source=None, ID=self.HVID)

    @inlineCallbacks
    def initData(self):
        self.gui.dac.setValue(voltage_list[i])
        self.gui.toggle.setChecked(toggle_list[i])

    def initGUI(self):
        # connect global signals
        self.gui.device_global_onswitch.clicked.connect(lambda: self.hp.toggle(-1, 1))
        self.gui.device_global_offswitch.clicked.connect(lambda: self.hp.toggle(-1, 0))
        self.gui.device_global_clear.clicked.connect(lambda: self.hp.clear())
        # connect each channel
        for channel in self.gui.amo8_channels:
            channel.dac.valueChanged.connect(lambda value: self.hp.voltage(channel.number, value))
            channel.ramp_start.clicked.connect(lambda voltage=channel.ramp_target.value(), rate=channel.ramp_rate.value():
                                               self.hp.ramp(channel.number, voltage, rate))
            channel.toggle.clicked.connect(lambda status=channel.lockswitch.isChecked():
                                           self.hp.toggle(channel.number, status))
            channel.resetswitch.clicked.connect(lambda: self.reset(channel.number))


    # SLOTS
    @inlineCallbacks
    def reset(self, channel_num):
        yield self.hp.voltage(channel_num, 0)
        yield self.hp.toggle(channel_num, 0)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(HP6256B_client)
