from time import time
from datetime import datetime
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.stability_gui import stability_gui

_PICKOFF_FACTOR = 300
_


class stability_client(GUIClient):

    name = 'Stability Client'
    servers = {'os': 'Oscilloscope Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = stability_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # find Rigol DS1000z oscilloscope
        # todo: connect to correct rigol oscope
        devices = yield self.os.list_devices()
        for dev_id in devices:
            dev_name = dev_id[1]
            if 'DS1Z' in dev_name:
                yield self.os.select_device(dev_name)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create loopingcall
        self.refresher = LoopingCall(self.updateVoltage)
        self.refresher.start(3, now=False)

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
    def updateValues(self):
        """
        Updates GUI when values are received from server.
        """
        # calculate voltage
        voltage_tmp = yield self.os.measure_amplitude(1)
        voltage_tmp = voltage_tmp / 2 * _PICKOFF_FACTOR
        self.gui.voltage_display.setText('{:.3f}'.format(voltage_tmp))
        # calculate a parameter

        # calculate q parameter
        # calculate secular frequency
        if self.recording:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, voltage_tmp, context=self.c_record)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(stability_client)
