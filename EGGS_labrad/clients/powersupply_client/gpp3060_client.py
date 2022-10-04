from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.powersupply_client.powersupply_gui import powersupply_gui


class gpp3060_client(GUIClient):

    name = 'GPP3060 Power Supply Client'

    VOLTAGEID = 984312
    TOGGLEID = 984311
    servers = {'gpp': 'GPP3060 Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = powersupply_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.pz.signal__voltage_update(self.VOLTAGEID)
        yield self.pz.addListener(listener=self.updateVoltage, source=None, ID=self.VOLTAGEID)
        yield self.pz.signal__toggle_update(self.TOGGLEID)
        yield self.pz.addListener(listener=self.updateToggle, source=None, ID=self.TOGGLEID)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

    @inlineCallbacks
    def initData(self):
        for i in range(4):
            channel_status = yield self.pz.toggle(i + 1)
            self.gui.channels[i].toggleswitch.setChecked(channel_status)
            channel_voltage = yield self.pz.voltage(i + 1)
            self.gui.channels[i].voltage.setValue(channel_voltage)

    def initGUI(self):
        for i in range(4):
            channel_widget = self.gui.channels[i]
            channel_widget.voltage.valueChanged.connect(lambda _voltage, _chan=i+1: self.pz.voltage(_chan, _voltage))
            channel_widget.toggleswitch.valueChanged.connect(lambda _status, _chan=i+1: self.pz.toggle(_chan, _status))


    # SLOTS
    def updateVoltage(self, c, msg):
        chan_num, _voltage = msg
        # need to convert channel number to index
        channel_voltage_widget = self.gui.channels[chan_num - 1].voltage
        channel_voltage_widget.blockSignals(True)
        channel_voltage_widget.setValue(_voltage)
        channel_voltage_widget.blockSignals(False)

    def updateToggle(self, c, msg):
        chan_num, _status = msg
        # need to convert channel number to index
        channel_switch_widget = self.gui.channels[chan_num - 1].toggleswitch
        channel_switch_widget.blockSignals(True)
        channel_switch_widget.setChecked(_status)
        channel_switch_widget.setAppearance(_status)
        channel_switch_widget.blockSignals(False)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(piezo_client)
