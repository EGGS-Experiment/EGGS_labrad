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
            self.gui = TTL_gui(device_db)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to signals
        yield self.aq.signal__ttl_changed(TTLID)
        yield self.aq.addListener(listener=self.updateTTLDisplay, source=None, ID=TTLID)

    #@inlineCallbacks
    def initData(self):
        pass

    def initGUI(self):
        for in:
            #channel_gui.toggleswitch.toggled.connect(lambda status, chan=channel_name: self.aq.ttl_set(chan, status))
            # todo set display on

    def updateTTLDisplay(self, c, signal):
        ttl_name, probe, status = signal
        if probe == 0:
            self.ttl_clients[ttl_name].lockswitch.setText('scde')


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(TTL_client)
