from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.piezo_client.piezo_gui import piezo_gui


class piezo_client(GUIClient):

    name = 'Piezo Client'

    VOLTAGEID = 984312
    servers = {'pz': 'Piezo Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = piezo_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.niops.signal__voltage_update(self.VOLTAGEID)
        yield self.niops.addListener(listener=self.updateVoltage, source=None, ID=self.VOLTAGEID)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

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
    def updateVoltage(self, c, voltage):
        # update voltage
        self.gui.ip_voltage_display.setText(str(voltage))

    def lock_ip(self, status):
        """
        Locks power status of ion pump.
        """
        self.gui.ip_voltage.setEnabled(status)
        self.gui.ip_power.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(piezo_client)
