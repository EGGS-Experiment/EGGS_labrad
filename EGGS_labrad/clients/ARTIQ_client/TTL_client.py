from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.ARTIQ_client.TTL_gui import TTL_gui

TTLID = 888999


class TTL_client(GUIClient):
    """
    Client for all TTL channels.
    """

    name = "ARTIQ TTL Client"
    servers = {'aq': 'ARTIQ Server'}


    def getgui(self):
        if self.gui is None:
            self.gui = TTL_gui(self.ttl_list)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # device dictionary: ttl_list holds a dictionary of all types of TTLs
        self.ttl_list = {
            "Input": {},
            "Output": {},
            "Urukul": {},
            "Other": {}
        }
        # parse device_db for TTLs
        self._getDevices(device_db)
        # connect to signals
        yield self.aq.signal__ttl_changed(TTLID)
        yield self.aq.addListener(listener=self.updateTTLDisplay, source=None, ID=TTLID)

    def _getDevices(self, device_db):
        for name, params in device_db.items():
            # only get devices with named class
            if 'class' not in params:
                continue
            # set device as attribute
            devicetype = params['class']
            if devicetype == 'TTLInOut':
                self.ttl_list["Input"][name] = None
            elif devicetype == 'TTLOut':
                other_names = ('zotino', 'led', 'sampler')
                if 'urukul' in name:
                    self.ttl_list["Urukul"][name] = None
                elif any(string in name for string in other_names):
                    self.ttl_list["Other"][name] = None
                else:
                    self.ttl_list["Output"][name] = None

    #@inlineCallbacks
    def initData(self):
        # todo: get values and set them on GUI
        pass

    def initGUI(self):
        ttl_all = {**self.ttl_list['Input'], **self.ttl_list['Output'], **self.ttl_list['Urukul'], **self.ttl_list['Other']}
        for channel_name, channel_gui in ttl_all.items():
            channel_gui.toggleswitch.toggled.connect(lambda status, chan=channel_name: self.aq.ttl_set(chan, status))
            channel_gui.lock(False)

    def updateTTLDisplay(self, c, signal):
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(TTL_client)
