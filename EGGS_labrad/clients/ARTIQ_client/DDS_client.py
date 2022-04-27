from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QFrame

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.ARTIQ_client.DDS_gui import DDS_gui


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
        # assign ad9910 channels to urukuls
        self.urukul_list = {}
        for device_name in ad9910_list:
            urukul_name = device_name.split('_')[0]
            if urukul_name not in self.urukul_list:
                self.urukul_list[urukul_name] = []
            self.urukul_list[urukul_name].append(device_name)

    @inlineCallbacks
    def initData(self):
        # todo: get values from server
        pass

    def initGUI(self):
        keys_tmp = list(self.urukul_list.keys())
        for i in range(len(keys_tmp)):
            urukul_name = keys_tmp[i]
            ad9910_list = self.urukul_list[urukul_name]
            urukul_group = self._makeUrukulGroup(urukul_name, ad9910_list)
            layout.addWidget(urukul_group, 2 + i, 0, 1, self.row_length)
            for i in range(len(ad9910_list)):
                # initialize GUIs for each channel
                channel_name = ad9910_list[i]
                channel_gui = AD9910_channel(channel_name)
                channel_gui.freq.valueChanged.connect(
                    lambda freq, chan=channel_name: self.artiq.dds_frequency(chan, freq * 1e6))
                channel_gui.ampl.valueChanged.connect(
                    lambda ampl, chan=channel_name: self.artiq.dds_amplitude(chan, ampl))
                channel_gui.att.valueChanged.connect(
                    lambda att, chan=channel_name: self.artiq.dds_attenuation(chan, att, 'v'))
                channel_gui.rfswitch.toggled.connect(
                    lambda status, chan=channel_name: self.artiq.dds_toggle(chan, status))


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DDS_client)
