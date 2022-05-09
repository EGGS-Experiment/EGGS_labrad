from time import time
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.cryovac_clients.twistorr74_gui import twistorr74_gui


class twistorr74_client(GUIClient):

    name = 'Twistorr74 Client'

    PRESSUREID = 694321
    TOGGLEID = 694322
    SPEEDID = 694323
    POWERID = 694324

    servers = {'tt': 'TwisTorr74 Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = twistorr74_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.tt.signal__pressure_update(self.PRESSUREID)
        yield self.tt.addListener(listener=self.updatePressure, source=None, ID=self.PRESSUREID)
        yield self.tt.signal__power_update(self.POWERID)
        yield self.tt.addListener(listener=self.updatePower, source=None, ID=self.POWERID)
        yield self.tt.signal__speed_update(self.SPEEDID)
        yield self.tt.addListener(listener=self.updateSpeed, source=None, ID=self.SPEEDID)
        yield self.tt.signal__toggle_update(self.TOGGLEID)
        yield self.tt.addListener(listener=self.updateToggle, source=None, ID=self.TOGGLEID)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        self.starttime = None
        # start device polling only if not already started
        poll_params = yield self.tt.polling()
        if not poll_params[0]:
            yield self.tt.polling(True, 5.0)

    @inlineCallbacks
    def initData(self):
        status_tmp = yield self.tt.toggle()
        self.gui.twistorr_toggle.setChecked(status_tmp)

    def initGUI(self):
        self.gui.twistorr_lockswitch.toggled.connect(lambda status: self.gui.twistorr_toggle.setEnabled(status))
        self.gui.twistorr_toggle.clicked.connect(lambda status: self.tt.toggle(status))
        self.gui.twistorr_record.toggled.connect(lambda status: self.record_pressure(status))
        # start up locked
        self.gui.twistorr_lockswitch.setChecked(False)
        self.gui._lock(False)


    # SIGNALS
    @inlineCallbacks
    def updatePressure(self, c, pressure):
        """
        Updates GUI when values are received from server.
        """
        self.gui.pressure_display.setText('{:.1e}'.format(pressure))
        if self.recording:
            elapsedtime = time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def updatePower(self, c, power):
        """
        Updates GUI when values are received from server.
        """
        self.gui.power_display.setText(str(power))

    def updateSpeed(self, c, speed):
        """
        Updates GUI when values are received from server.
        """
        self.gui.speed_display.setText(str(speed))

    def updateToggle(self, c, status):
        """
        Updates GUI when other clients have made changes to the device.
        """
        self.gui.twistorr_toggle.setChecked(status)


    # SLOTS
    @inlineCallbacks
    def record_pressure(self, status):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if status:
            self.starttime = time()
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new('Twistorr 74 Pump Controller', [('Elapsed time', 't')],
                              [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_record)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(twistorr74_client)
