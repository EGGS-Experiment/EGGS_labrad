from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.ARTIQ_client.DDS_gui import AD9910_channel


class AD9910_client(GUIClient):
    """
    Client for a single DDS channel.
    """

    name = "AD9910 Client"
    servers = {'aq': 'ARTIQ Server'}
    dds_name = 'urukul0_ch0'

    def getgui(self):
        if self.gui is None:
            self.gui = AD9910_channel(self.dds_name)
        return self.gui

    #@inlineCallbacks
    def initClient(self):
        pass

    #@inlineCallbacks
    def initData(self):
        #todo: read register values from artiq
        pass

    def initGUI(self):
        self.gui.freq.valueChanged.connect(lambda freq, chan=self.dds_name: self.artiq.dds_frequency(chan, freq))
        self.gui.ampl.valueChanged.connect(lambda ampl, chan=self.dds_name: self.artiq.dds_amplitude(chan, ampl))
        self.gui.att.valueChanged.connect(lambda att, chan=self.dds_name: self.artiq.dds_attenuation(chan, att, 'v'))
        self.gui.rfswitch.toggled.connect(lambda status, chan=self.dds_name: self.artiq.dds_toggle(chan, status))
        self.gui.lock(False)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(AD9910_client)
