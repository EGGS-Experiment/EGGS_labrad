import time
import datetime as datetime

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.cryovac_clients.f70_gui import f70_gui


class f70_client(f70_gui):

    name = 'F70 Client'

    TEMPID = 109621
    PRESSUREID = 109622

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        self.servers = ['F70 Server', 'Data Vault']
        # initialization sequence
        d = self.connect()
        d.addCallback(self.initData)
        d.addCallback(self.initGUI)

    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to pump servers
        and relevant labrad servers
        """
        # create labrad connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        # try to get servers
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
            self.f70 = self.cxn.f70_server
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        # connect to signals
            # device parameters
        yield self.f70.signal__pressure_update(self.PRESSUREID)
        yield self.f70.addListener(listener=self.updatePressure, source=None, ID=self.PRESSUREID)
        yield self.f70.signal__temperature_update(self.TEMPID)
        yield self.f70.addListener(listener=self.updateTemperature, source=None, ID=self.TEMPID)
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        # start device polling
        poll_params = yield self.f70.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.f70.polling(True, 5.0)
        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        status_list = yield self.f70.status()
        power_status = bool(status_list[0][-1])
        self.gui.power_button.setChecked(power_status)
        return self.cxn

    def initGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        self.gui.lockswitch.clicked.connect(lambda status: self.lock(status))
        self.gui.power_button.clicked.connect(lambda status: self.f70.toggle(status))
        self.gui.coldhead_pause.clicked.connect(lambda status: self.f70.cold_head_pause(status))
        self.gui.reset_button.clicked.connect(lambda status: self.f70.reset())
        self.gui.record_button.toggled.connect(lambda status: self.record(status))
        return self.cxn


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            yield self.initData(self.cxn)
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)

    def updatePressure(self, c, pressure):
        """
        Updates GUI when values are received from server.
        """
        self.gui.pressure_display_channel_1.setText(str(pressure[0]))
        self.gui.pressure_display_channel_2.setText(str(pressure[1]))

    def updateTemperature(self, c, temp):
        """
        Updates GUI when values are received from server.
        """
        for i in range(4):
            self.gui.temperature_display_channels[i].setText(str(temp[i]))


    # SLOTS
    @inlineCallbacks
    def record(self, status):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording == True:
            self.starttime = time.time()
            date = datetime.now()
            year = str(date.year)
            month = '{:02d}'.format(date.month)

            trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
            trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('F70 Helium Compressor', [('Elapsed time', 't')],
                              [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_record)

    def lock(self, status):
        """
        Locks user interface to device.
        """
        self.gui.power_button.setEnabled(status)
        self.gui.coldhead_pause.setEnabled(status)
        self.gui.reset_button.setEnabled(status)


    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(f70_client)
