from time import time
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.cryovac_clients.niops03_gui import niops03_gui


class niops03_client(GUIClient):

    name = 'NIOPS03 Client'

    PRESSUREID = 878352
    VOLTAGEID = 878353
    TEMPERATUREID = 878354
    IPPOWERID = 878355
    NPPOWERID = 878356

    servers = {'niops': 'NIOPS03 Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = niops03_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.niops.signal__pressure_update(self.PRESSUREID)
        yield self.niops.addListener(listener=self.updatePressure, source=None, ID=self.PRESSUREID)
        yield self.niops.signal__voltage_update(self.VOLTAGEID)
        yield self.niops.addListener(listener=self.updateVoltage, source=None, ID=self.VOLTAGEID)
        yield self.niops.signal__temperature_update(self.TEMPERATUREID)
        yield self.niops.addListener(listener=self.updateTemperature, source=None, ID=self.TEMPERATUREID)
        yield self.niops.signal__ip_power_update(self.IPPOWERID)
        yield self.niops.addListener(listener=self.updateIPPower, source=None, ID=self.IPPOWERID)
        yield self.niops.signal__np_power_update(self.NPPOWERID)
        yield self.niops.addListener(listener=self.updateNPPower, source=None, ID=self.NPPOWERID)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # start device polling
        poll_params = yield self.niops.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.niops.polling(True, 5.0)

    @inlineCallbacks
    def initData(self):
        # IP/NP power
        device_status = yield self.niops.status()
        device_status = device_status.strip().split(', ')
        device_status = [text.split(' ') for text in device_status]
        device_status = {val[0]: val[1] for val in device_status}
        ip_on = True if device_status['IP'] == 'ON' else False
        np_on = True if device_status['NP'] == 'ON' else False
        self.gui.ip_power.setChecked(ip_on)
        self.gui.np_power.setChecked(np_on)
        # IP voltage
        v_ip = yield self.niops.ip_voltage()
        self.gui.ip_voltage_display.setText(str(v_ip))
        self.gui.ip_voltage.setEnabled(ip_on)

    def initGUI(self):
        # ion pump
        self.gui.ip_lockswitch.toggled.connect(lambda status: self.lock_ip(status))
        self.gui.ip_power.clicked.connect(lambda status: self.toggle_ni(status))
        self.gui.ip_record.toggled.connect(lambda status: self.record_pressure(status))
        self.gui.ip_voltage.valueChanged.connect(lambda voltage: self.niops.ip_voltage(int(voltage)))
        # getter
        self.gui.np_lockswitch.toggled.connect(lambda status: self.gui.np_power.setEnabled(status))
        self.gui.np_mode.currentIndexChanged.connect(lambda index: self.niops.np_mode(index + 1))
        self.gui.np_power.clicked.connect(lambda status: self.niops.np_toggle(status))
        # lock on startup
        self.gui.ip_lockswitch.setChecked(False)
        self.gui.np_lockswitch.setChecked(False)


    # SLOTS
    @inlineCallbacks
    def updatePressure(self, c, pressure):
        # update pressure
        self.gui.ip_pressure_display.setText('{:.1e}'.format(pressure))
        if self.recording:
            elapsedtime = time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def updateVoltage(self, c, voltage):
        # update voltage
        self.gui.ip_voltage_display.setText(str(voltage))

    def updateTemperature(self, c, temperatures):
        # update temperature
        self.gui.ip_temperature_display.setText(str(temperatures[0]))
        self.gui.np_temperature_display.setText(str(temperatures[1]))

    def updateIPPower(self, c, power):
        # set IP power
        self.gui.ip_voltage.setEnabled(power)
        self.gui.ip_power.setEnabled(False)
        self.gui.ip_power.setChecked(power)
        self.gui.ip_power.setEnabled(True)

    def updateNPPower(self, c, power):
        # set NP power
        self.gui.np_power.setEnabled(False)
        self.gui.np_power.setChecked(power)
        self.gui.np_power.setEnabled(True)

    @inlineCallbacks
    def record_pressure(self, status):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording:
            self.starttime = time()
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new('NIOPS03 Pump', [('Elapsed time', 's')], [('Ion Pump', 'Pressure', 'mbar')],
                              context=self.c_record)

    @inlineCallbacks
    def toggle_ni(self, status):
        """
        Sets ion pump power on or off.
        """
        self.gui.ip_voltage.setEnabled(status)
        yield self.niops.ip_toggle(status)

    def lock_ip(self, status):
        """
        Locks power status of ion pump.
        """
        self.gui.ip_voltage.setEnabled(status)
        self.gui.ip_power.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(niops03_client)
