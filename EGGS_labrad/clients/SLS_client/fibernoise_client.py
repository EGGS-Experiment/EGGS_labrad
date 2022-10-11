from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.SLS_client.fibernoise_gui import fibernoise_gui
# todo: support max/ovp
_OSCOPE_NAME = "DS1ZC221401223"
_OSCOPE_CHANNEL = 1


class fibernoise_client(GUIClient):

    name = 'SLS Fiber Noise Client'
    servers = {'os': 'Oscilloscope Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = fibernoise_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        dev_list = yield self.os.list_devices()

        # connect to correct oscilloscope
        for dev_num, dev_name in dev_list:
            if _OSCOPE_NAME in dev_name:
                yield self.os.select_device(dev_num)

    def initGUI(self):
        # connect signals
        self.gui.trace_button.clicked.connect(lambda: self.display_trace())
        self.gui.save_button.clicked.connect(lambda: self.save_trace())


    # SLOTS
    def display_trace(self):
        """
        Pulls a trace from the oscilloscope displaying the fiber noise error
            and displays it on the GUI.
        """
        pass

    def save_trace(self):
        """
        Saves the current trace to the data vault.
        """
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(fibernoise_client)
