import os
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.cryovac_clients.niops03_gui import niops03_gui

class niops03_client(niops03_gui):
    name = 'NIOPS03 Client'

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        d = self.connect()
        d.addCallback(self.initializeGUI)

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad
        """
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        self.reg = self.cxn.registry
        self.dv = self.cxn.data_vault
        self.niops = self.cxn.niops03_server

        # get polling time
        # yield self.reg.cd(['Clients', self.name])
        # self.poll_time = yield float(self.reg.get('poll_time'))
        self.poll_time = 5.0

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        #create and start loop to poll server for temperature
        self.poll_loop = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(1.0, self.start_polling)

        return self.cxn

    @inlineCallbacks
    def initializeGUI(self, cxn):
        #startup data
            #IP/NP power
        device_status = yield self.niops.status()
        device_status = device_status.strip().split(', ')
        device_status = [text.split(' ') for text in device_status]
        device_status = {val[0]: val[1] for val in device_status}
        ip_on = True if device_status['IP'] == 'ON' else False
        np_on = True if device_status['NP'] == 'ON' else False
        self.gui.niops_power.setChecked(ip_on)
        self.gui.np_power.setChecked(np_on)
            #IP voltage
        v_ip = yield self.niops.ip_voltage()
        self.gui.niops_voltage.setValue(v_ip)
        #connect signals to slots
            #ion pump
        self.gui.niops_lockswitch.toggled.connect(lambda status: self.lock_niops(status))
        self.gui.niops_power.toggled.connect(lambda status: self.toggle_niops(status))
        self.gui.niops_record.toggled.connect(lambda status: self.record_pressure(status))
        self.gui.niops_voltage.valueChanged.connect(lambda voltage: self.set_ip_voltage(voltage))
            #getter
        self.gui.np_lockswitch.toggled.connect(lambda status: self.lock_np(status))
        self.gui.np_power.toggled.connect(lambda status: self.toggle_np(status))

    #Slot functions
    @inlineCallbacks
    def record_pressure(self, status):
        """
        Creates a new dataset to record pressure and tells polling loop
        to add data to data vault
        """
        self.recording = status
        if self.recording == True:
            self.starttime = time.time()
            date = datetime.datetime.now()
            year = str(date.year)
            month = '%02d' % date.month  # Padded with a zero if one digit
            day = '%02d' % date.day  # Padded with a zero if one digit
            hour = '%02d' % date.hour  # Padded with a zero if one digit
            minute = '%02d' % date.minute  # Padded with a zero if one digit

            trunk1 = year + '_' + month + '_' + day
            trunk2 = self.name + '_' + hour + ':' + minute
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('NIOPS03 Pump', [('Elapsed time', 's')], \
                                       [('Ion Pump', 'Pressure', 'mbar')], context=self.c_record)

    @inlineCallbacks
    def toggle_niops(self, status):
        """
        Sets ion pump power on or off.
        """
        yield self.niops.toggle_ip(status)

    def lock_niops(self, status):
        """
        Locks power status of ion pump.
        """
        self.gui.niops_voltage.setEnabled(status)
        self.gui.niops_power.setEnabled(status)

    #@inlineCallbacks
    def set_ip_voltage(self, voltage):
        """
        Sets the ion pump voltage.
        """
        yield self.niops.ip_voltage(voltage)

    @inlineCallbacks
    def toggle_np(self, status):
        """
        Sets getter power on or off.
        """
        yield self.niops.toggle_np(status)

    def lock_np(self, status):
        """
        Locks power status of getter.
        """
        self.gui.np_power.setEnabled(status)


    #Polling functions
    def start_polling(self):
        self.poll_loop.start(self.poll_time)

    def stop_polling(self):
        self.poll_loop.stop()

    @inlineCallbacks
    def poll(self):
        pressure = yield self.niops.ip_pressure()
        self.gui.niops_pressure_display.setText(str(pressure))
        if True:
        # if self.gui.niops_power.isChecked():
            workingtime = yield self.niops.working_time()
            workingtime_ip = str(workingtime[0][0]) + ':' + str(workingtime[0][1])
            workingtime_np = str(workingtime[1][0]) + ':' + str(workingtime[1][1])
            self.gui.niops_workingtime_display.setText(workingtime_ip)
            self.gui.np_workingtime_display.setText(workingtime_np)
        if self.recording == True:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(niops03_client)
