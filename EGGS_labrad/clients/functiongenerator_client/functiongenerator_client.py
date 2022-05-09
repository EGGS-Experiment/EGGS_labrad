from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.functiongenerator_client.functiongenerator_gui import functiongenerator_gui

from twisted.internet.defer import inlineCallbacks


class functiongenerator_client(GUIClient):
    """
    Stripped client for a function generator.
    """

    name = "Agilent 33210A Client"
    servers = {'fg': 'Function Generator Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = functiongenerator_gui("Tickle Client")
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # find Agilent 33210A function generator
        devices = yield self.fg.list_devices()
        for dev_id in devices:
            dev_name = dev_id[1]
            if '48007979' in dev_name:
                yield self.fg.select_device(dev_name)

    @inlineCallbacks
    def initData(self):
        freq_val = yield self.fg.frequency()
        ampl_val = yield self.fg.amplitude()
        toggle_val = yield self.fg.toggle()
        # frequency is in kHz
        self.gui.freq.setValue(freq_val / 1000)
        self.gui.ampl.setValue(ampl_val)
        self.gui.rfswitch.setChecked(toggle_val)

    def initGUI(self):
        # frequency is in kHz
        self.gui.freq.valueChanged.connect(lambda freq: self.fg.frequency(freq * 1000))
        self.gui.ampl.valueChanged.connect(lambda ampl: self.fg.amplitude(ampl))
        self.gui.rfswitch.toggled.connect(lambda status: self.fg.toggle(status))
        self.gui.lock(False)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(functiongenerator_client)
