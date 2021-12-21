import time
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.cryovac_clients.fma1700a_gui import fma1700a_gui


class fma1700a_client(fma1700a_gui):

    name = 'FMA1700A Client'
    FLOWID = 877920

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        self.servers = ['FMA1700A Server', 'Data Vault']
        # initialization sequence
        d = self.connect()
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)


    # SETUP
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad.
        """
        # create labrad connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        # try to get servers
        try:
            self.dv = self.cxn.data_vault
            self.fma = self.cxn.fma1700a_server
        except Exception as e:
            print(e)
            raise

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        # connect to signals
            # device parameters
        yield self.fma.signal__flow_update(self.FLOWID)
        yield self.fma.addListener(listener=self.updateFlow, source=None, ID=self.FLOWID)
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)

        # start device polling
        poll_params = yield self.fma.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.fma.polling(True, 5.0)
        return self.cxn

    #@inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        return self.cxn

    def initializeGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        self.gui.record_button.toggled.connect(lambda status: self.record_flow(status))
        return self.cxn


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            # get latest values
            yield self.initData(self.cxn)
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)


    # SLOTS
    @inlineCallbacks
    def record_flow(self, status):
        """
        Creates a new dataset to record flow and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording:
            self.starttime = time.time()
            date = datetime.now()
            year = str(date.year)
            month = '{:02d}'.format(date.month)

            trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
            trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('FMA1700A Flowmeter', [('Elapsed time', 't')],
                                       [('Flowmeter', 'Flow rate', 'L/min')], context=self.c_record)

    @inlineCallbacks
    def updateFlow(self, c, flow):
        """
        Updates GUI when values are received from server.
        """
        self.gui.flow_display.setText(str(flow))
        if self.recording:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, flow, context=self.c_record)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(fma1700a_client)
