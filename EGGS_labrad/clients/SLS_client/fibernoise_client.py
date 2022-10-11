from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.SLS_client.fibernoise_gui import fibernoise_gui
# todo: support max/ovp


class fibernoise_client(GUIClient):

    name = 'SLS Fiber Noise Client'
    servers = {'os': 'Oscilloscope Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = fibernoise_gui()
        return self.gui

    def initGUI(self):
        # connect signals
        self.gui.toggleswitch.clicked.connect(lambda _status: self.gpp.channel_toggle(_status))
        self.gui.voltageSet.valueChanged.connect(lambda _voltage: self.gpp.channel_voltage(_voltage))
        self.gui.currentSet.valueChanged.connect(lambda _current: self.gpp.channel_current(_current))


    # SLOTS
    def updateMode(self, c, msg):
        chan_num, mode = msg
        widget = self.gui.channels[chan_num - 1].voltage

        # todo: convert mode to index

        # correctly set value
        widget.blockSignals(True)
        widget.setValue(mode)
        widget.blockSignals(False)



if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(fibernoise_client)
