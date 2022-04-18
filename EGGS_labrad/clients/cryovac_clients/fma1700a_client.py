from time import time
from datetime import datetime
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.cryovac_clients.fma1700a_gui import fma1700a_gui


class fma1700a_client(GUIClient):

    name = 'FMA1700A Client'
    FLOWID = 877920
    servers = {'fma': 'FMA1700A Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = fma1700a_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # connect to signals
        yield self.fma.signal__flow_update(self.FLOWID)
        yield self.fma.addListener(listener=self.updateFlow, source=None, ID=self.FLOWID)
        # start device polling if not already started
        poll_params = yield self.fma.polling()
        if not poll_params[0]:
            yield self.fma.polling(True, 5.0)

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
            yield self.dv.new('FMA1700A Flowmeter', [('Elapsed time', 't')],
                                       [('Flowmeter', 'Flow rate', 'L/min')], context=self.c_record)

    @inlineCallbacks
    def updateFlow(self, c, flow):
        """
        Updates GUI when values are received from server.
        """
        self.gui.flow_display.setText(str(flow))
        if self.recording:
            elapsedtime = time() - self.starttime
            yield self.dv.add(elapsedtime, flow, context=self.c_record)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(fma1700a_client)
