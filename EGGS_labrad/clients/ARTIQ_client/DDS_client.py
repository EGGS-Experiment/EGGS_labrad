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
    servers = {'aq': 'ARTIQ Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = DDS_gui(self.urukul_list)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # device dictionaries
        self.urukul_list = {}
        # parse device_db for TTLs
        self._getDevices(device_db)
        yield self.aq.signal__dds_changed(DDSID)
        yield self.aq.addListener(listener=self.updateDDS, source=None, ID=DDSID)

    def _getDevices(self, device_db):
        # get devices
        for name, params in device_db.items():
            if 'class' not in params:
                continue
            elif params['class'] == 'CPLD':
                self.urukul_list[name] = {}
            elif params['class'] == 'AD9910':
                # assign ad9910 channels to urukuls
                urukul_name = params["arguments"]["cpld_device"]
                if urukul_name not in self.urukul_list:
                    self.urukul_list[urukul_name] = {}
                self.urukul_list[urukul_name][name] = None

    #@inlineCallbacks
    def initData(self):
        # todo: get switch, att, freq, amp, phase values from server
        pass

    def initGUI(self):
        # connect an urukul group
        for urukul_name, ad9910_list in self.gui.urukul_list.items():
            # connect all DDS channels within an urukul group
            for ad9910_name, ad9910_widget in ad9910_list.items():
                # initialize the ad9910 GUIs within an urukul group
                ad9910_widget.freq.valueChanged.connect(lambda freq, _channel_name=ad9910_name:
                                                        self.aq.dds_frequency(_channel_name, freq * 1e6))
                ad9910_widget.ampl.valueChanged.connect(lambda ampl, _channel_name=ad9910_name:
                                                        self.aq.dds_amplitude(_channel_name, ampl))
                ad9910_widget.att.valueChanged.connect(lambda att, _channel_name=ad9910_name:
                                                       self.aq.dds_attenuation(_channel_name, att, 'v'))
                ad9910_widget.rfswitch.toggled.connect(lambda status, _channel_name=ad9910_name:
                                                       self.aq.dds_toggle(_channel_name, status))
                ad9910_widget.lock(False)

    def updateDDS(self, c, signal):
        ad9910_name, param, val = signal
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DDS_client)
