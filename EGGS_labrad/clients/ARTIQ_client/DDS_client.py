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

    @inlineCallbacks
    def initData(self):
        # get minimum attenuations from registry
        min_attenuations = {}
        yield self.reg.cd(['', 'Clients', 'ARTIQ', 'Urukul'])
        _, restricted_dds_channels = yield self.reg.dir()
        for dds_channel in restricted_dds_channels:
            min_attenuations[dds_channel] = yield self.reg.get(dds_channel)
        for urukul_name, ad9910_list in self.urukul_list.items():
            for ad9910_name, ad9910_widget in ad9910_list.items():
                # check if this channel has a restricted attenuation range
                if ad9910_name in min_attenuations:
                    ad9910_widget.att.setMinimum(min_attenuations[ad9910_name])
                # get values
                sw_status = yield self.aq.dds_toggle(ad9910_name)
                att_mu = yield self.aq.dds_attenuation(ad9910_name)
                freq_mu = yield self.aq.dds_frequency(ad9910_name)
                ampl_mu = yield self.aq.dds_amplitude(ad9910_name)
                # convert from machine units to human units
                att_dbm = (255 - (att_mu & 0xff)) / 8
                freq_mhz = freq_mu / 4.2949673
                ampl_pct = ampl_mu / 0x3fff
                # set values
                ad9910_widget.rfswitch.setChecked(sw_status)
                ad9910_widget.att.setValue(att_dbm)
                ad9910_widget.freq.setValue(freq_mhz / 1e6)
                ad9910_widget.ampl.setValue(ampl_pct * 1e2)

    def initGUI(self):
        # connect an urukul group
        for urukul_name, ad9910_list in self.gui.urukul_list.items():
            button = getattr(self.gui, "{:s}_init".format(urukul_name))
            button.clicked.connect(lambda _name=urukul_name: self.aq.urukul_initialize(_name))
            # connect DDS channels
            for ad9910_name, ad9910_widget in ad9910_list.items():
                ad9910_widget.initbutton.clicked.connect(lambda status, _channel_name=ad9910_name: self.aq.dds_initialize(_channel_name))
                ad9910_widget.freq.valueChanged.connect(lambda freq, _channel_name=ad9910_name:
                                                        self.aq.dds_frequency(_channel_name, freq * 1e6))
                ad9910_widget.ampl.valueChanged.connect(lambda ampl, _channel_name=ad9910_name:
                                                        self.aq.dds_amplitude(_channel_name, ampl / 100))
                ad9910_widget.att.valueChanged.connect(lambda att, _channel_name=ad9910_name:
                                                       self.aq.dds_attenuation(_channel_name, att))
                ad9910_widget.rfswitch.clicked.connect(lambda status, _channel_name=ad9910_name:
                                                       self.aq.dds_toggle(_channel_name, status))
                ad9910_widget.lock(False)

    def updateDDS(self, c, signal):
        ad9910_name, param, val = signal
        ad9910_names = [ad9910_name for ad9910_list in self.urukul_list.values() for ad9910_name in ad9910_list.keys()]
        if ad9910_name in ad9910_names:
            # todo: get widget
            # todo: lock gui
            # todo: update values
            # todo: set previous enabled state
            print('name:', ad9910_name)
            print('param:', param)
            print('val:', val)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DDS_client)
