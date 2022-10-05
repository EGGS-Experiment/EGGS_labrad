from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.powersupply_client.powersupply_gui import powersupply_gui
# todo: support max/ovp


class gpp3060_client(GUIClient):

    name = 'GPP3060 Power Supply Client'

    TOGGLEID =  130944
    MODEID =    130943
    ACTUALID =  130942
    SETID =     130941
    MAXID =   130940
    servers = {'gpp': 'GPP3060 Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = powersupply_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.gpp.signal__toggle_update(self.TOGGLEID)
        yield self.gpp.addListener(listener=self.updateToggle, source=None, ID=self.TOGGLEID)
        #yield self.gpp.signal__mode_update(self.MODEID)
        #yield self.gpp.addListener(listener=self.updateMode, source=None, ID=self.MODEID)
        yield self.gpp.signal__actual_update(self.ACTUALID)
        yield self.gpp.addListener(listener=self.updateActual, source=None, ID=self.ACTUALID)
        yield self.gpp.signal__set_update(self.SETID)
        yield self.gpp.addListener(listener=self.updateSet, source=None, ID=self.SETID)
        #yield self.gpp.signal__max_update(self.MAXID)
        #yield self.gpp.addListener(listener=self.updateMax, source=None, ID=self.MAXID)

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

    @inlineCallbacks
    def initData(self):
        for i in range(3):
            widget = self.gui.channels[i]

            # get values
            channel_status = yield self.gpp.toggle(i + 1)
            channel_voltage = yield self.gpp.channel_voltage(i + 1)
            channel_current = yield self.gpp.channel_current(i + 1)

            # set values
            widget.toggleswitch.setChecked(channel_status)
            widget.voltageSet.setValue(channel_voltage)
            widget.currentSet.setValue(channel_current)

    def initGUI(self):
        # configure channel 3 display (the 5V channel)
        self.gui.channels[2].voltageDisp.setText("5.00")

        # connect regular signals
        for i in range(3):
            channel_widget = self.gui.channels[i]
            channel_widget.toggleswitch.valueChanged.connect(lambda _status, _chan=i+1: self.gpp.channel_toggle(_chan, _status))
            channel_widget.voltageSet.valueChanged.connect(lambda _voltage, _chan=i+1: self.gpp.channel_voltage(_chan, _voltage))
            channel_widget.currentSet.valueChanged.connect(lambda _current, _chan=i+1: self.gpp.channel_current(_chan, _current))


    # SLOTS
    def updateToggle(self, c, msg):
        chan_num, _status = msg
        # need to convert channel number to index
        channel_switch_widget = self.gui.channels[chan_num - 1].toggleswitch
        channel_switch_widget.blockSignals(True)
        channel_switch_widget.setChecked(_status)
        channel_switch_widget.setAppearance(_status)
        channel_switch_widget.blockSignals(False)

    def updateMode(self, c, msg):
        chan_num, mode = msg
        widget = self.gui.channels[chan_num - 1].voltage

        # todo: convert mode to index

        # correctly set value
        widget.blockSignals(True)
        widget.setValue(mode)
        widget.blockSignals(False)

    def updateActual(self, c, msg):
        val_name, chan_num, value = msg

        # get correct widget & set value
        widget = None
        if val_name == 'I':
            widget = self.gui.channels[chan_num - 1].currentDisp
        elif val_name == 'V':
            widget = self.gui.channels[chan_num - 1].voltDisp
        widget.setText(str(value))

    def updateSet(self, c, msg):
        val_name, chan_num, value = msg

        # get correct widget
        widget = None
        if val_name == 'I':
            widget = self.gui.channels[chan_num - 1].currentDisp
        elif val_name == 'V':
            widget = self.gui.channels[chan_num - 1].voltDisp

        # set value
        widget.blockSignal(True)
        widget.setValue(value)
        widget.blockSignal(False)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(gpp3060_client)
