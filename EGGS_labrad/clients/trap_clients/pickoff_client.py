from time import time
from datetime import datetime
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.pickoff_gui import pickoff_gui

VOLTAGEID = 788135


class pickoff_client(GUIClient):

    name = 'Pickoff Client'
    servers = {'os': 'Oscilloscope Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = pickoff_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to oscilloscope
        yield self.os.select_device()
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create loopingcall

    def initGUI(self):
        self.gui.record_button.toggled.connect(lambda status: self.record_flow(status))


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
            self.starttime = time()
            date = datetime.now()
            year = str(date.year)
            month = '{:02d}'.format(date.month)
            trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
            trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('Helical Resonator Pickoff', [('Elapsed time', 't')],
                              [('Pickoff', 'Peak-Peak Voltage', 'V')], context=self.c_record)

    @inlineCallbacks
    def updateVoltage(self, voltage):
        """
        Updates GUI when values are received from server.
        """
        self.gui.voltage_display.setText(str(voltage))
        if self.recording:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, voltage, context=self.c_record)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(pickoff_client)
