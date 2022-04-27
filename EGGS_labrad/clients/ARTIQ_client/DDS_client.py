from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.ARTIQ_client.DDS_gui import DDS_gui

DDSID = 659313


class DDS_client(GUIClient):
    """
    Client for all Urukuls.
    """
    name = "Urukuls Client"
    row_length = 6
    servers = {'aq': 'ARTIQ Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = DDS_gui(device_db)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to signal
        yield self.aq.signal__dds_changed(DDSID)
        yield self.aq.addListener(listener=self.updateDDS, source=None, ID=DDSID)

    #@inlineCallbacks
    def initData(self):
        # todo: get switch, att, freq, amp, phase values from server
        pass

    def initGUI(self):
        # initialize and urukul group
        for urukul_name, ad9910_list in self.gui.urukul_list.items():
            for ad9910_name, ad9910_widget in ad9910_list.items():
                # initialize the ad9910 GUIs within an urukul group
                ad9910_widget.freq.valueChanged.connect(lambda freq, _channel_name=ad9910_name:
                                                        self.artiq.dds_frequency(_channel_name, freq * 1e6))
                ad9910_widget.ampl.valueChanged.connect(lambda ampl, _channel_name=ad9910_name:
                                                        self.artiq.dds_amplitude(_channel_name, ampl))
                ad9910_widget.att.valueChanged.connect(lambda att, _channel_name=ad9910_name:
                                                       self.artiq.dds_attenuation(_channel_name, att, 'v'))
                ad9910_widget.rfswitch.toggled.connect(lambda status, _channel_name=ad9910_name:
                                                       self.artiq.dds_toggle(_channel_name, status))


    def updateDDS(self, c, signal):
        ad9910_name, param, val = signal
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DDS_client)
