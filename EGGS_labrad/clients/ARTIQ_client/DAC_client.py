from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.ARTIQ_client.DAC_gui import DAC_gui


#todo signal

class DAC_client(GUIClient):
    """
    Client for an ARTIQ Fastino/Zotino board.
    """
    
    name = "Fastino Client"
    row_length = 6
    servers = {'aq': 'ARTIQ Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = DAC_gui(device_db)
        return self.gui
    
    @inlineCallbacks
    def initClient(self):
        # todo: connect to signals
        pass

    #@inlineCallbacks
    def initData(self):
        # todo: read DAC register values and update
        #yield self.aq.dds_list()
        for channel in self.gui.ad5372_clients.values():
            channel.lock(False)
            # todo: finish
        pass
    
    def initGUI(self):
        # todo: fix
        sezotino_global_ofs.valueChanged.connect(lambda voltage_mu: self.aq.dac_ofs(voltage_mu, 'mu'))
        for channel_name, channel_gui in self.gui.ad5372_clients.items():
            channel_num = int((channel_name.split('_'))[1])
            channel_gui.dac.valueChanged.connect(lambda voltage_mu, _channel_num=channel_num: self.aq.dac_set(_channel_num, voltage_mu, 'mu'))
            channel_gui.off.valueChanged.connect(lambda voltage_mu, _channel_num=channel_num: self.aq.dac_offset(_channel_num, voltage_mu, 'mu'))
            channel_gui.gain.valueChanged.connect(lambda gain_mu, _channel_num=channel_num: self.aq.dac_offset(_channel_num, gain_mu, 'mu'))
            channel_gui.resetswitch.clicked.connect(lambda _channel_num=channel_num: self.reset(_channel_num))
            #channel_gui.calibrateswitch.clicked.connect(lambda: self.calibrate)

    @inlineCallbacks
    def reset(self, channel_num):
        yield self.aq.dac_set(channel_num, 0, 'mu')
        yield self.aq.dac_offset(channel_num, 0, 'mu')
        yield self.aq.dac_set(channel_num, 0, 'mu')


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DAC_client)
