from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.ARTIQ_client.DAC_gui import DAC_gui

from copy import deepcopy

DACID = 659312


class DAC_client(GUIClient):
    """
    Client for an ARTIQ Fastino/Zotino board.
    """
    
    name = "Fastino Client"
    servers = {'aq': 'ARTIQ Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = DAC_gui(self.dac_list)
        return self.gui
    
    @inlineCallbacks
    def initClient(self):
        # device dictionary
        self.dac_list = {}
        # get devices
        self._getDevices(device_db)
        # connect to signals
        yield self.aq.signal__dac_changed(DACID)
        yield self.aq.addListener(listener=self.updateChannel, source=None, ID=DACID)

    def _getDevices(self, device_db):
        # get devices
        for name, params in device_db.items():
            if 'class' not in params:
                continue
            elif params['class'] in ('Zotino', 'Fastino'):
                self.dac_list[name] = {}

    #@inlineCallbacks
    def initData(self):
        # todo: read DAC register values and update
        pass
    
    def initGUI(self):
        # todo: fix global ofs
        self.gui.zotino_global_ofs.valueChanged.connect(lambda voltage_mu: self.aq.dac_ofs(voltage_mu, 'mu'))
        for dac_name, dac_channels in self.dac_list.items():
            for channel_num, channel_gui in dac_channels.items():
                channel_gui.dac.valueChanged.connect(lambda voltage_mu, _channel_num=channel_num:
                                                     self.aq.dac_set(_channel_num, voltage_mu, 'mu'))
                channel_gui.resetswitch.clicked.connect(lambda _channel_num=channel_num:
                                                        self.aq.dac_set(_channel_num, 0, 'mu'))
                if "ZOTINO" in dac_name.upper():
                    channel_gui.off.valueChanged.connect(lambda voltage_mu, _channel_num=channel_num:
                                                         self.aq.dac_offset(_channel_num, voltage_mu, 'mu'))
                    channel_gui.gain.valueChanged.connect(lambda gain_mu, _channel_num=channel_num:
                                                          self.aq.dac_offset(_channel_num, gain_mu, 'mu'))
                    channel_gui.calibrateswitch.clicked.connect(lambda: self.calibrate)
                # lock widgets on startup
                channel_gui.lock(False)

    def updateChannel(self, c, signal):
        num, param, val = signal
        channel_gui = self.gui.channel_widgets[num]
        gui_element = None
        if param == 'dac':
            gui_element = channel_gui.dac
        elif param == 'gain':
            gui_element = channel_gui.dac
        elif param == 'off':
            gui_element = channel_gui.dac
        elif param == 'ofs':
            gui_element = channel_gui.zotino_global_ofs
        # adjust value without causing the signal to trigger
        gui_element.setEnabled(False)
        gui_element.setValue(val)
        gui_element.setEnabled(True)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DAC_client)
