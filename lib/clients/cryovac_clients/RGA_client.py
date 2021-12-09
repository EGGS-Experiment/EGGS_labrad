from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.cryovac_clients.RGA_gui import RGA_gui

from datetime import datetime


class RGA_client(RGA_gui):

    name = 'RGA Client'
    # AUTOLOCKID = 295372

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.gui.setupUi()
        self.reactor = reactor
        self.servers = ['RGA Server', 'Data Vault']
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
        # create connection to labrad manager
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        # get servers
        try:
            self.dv = self.cxn.data_vault
            self.reg = self.cxn.registry
            self.rga = self.cxn.rga_server
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)

        # connect to signals
            # device parameters
        yield self.rga.signal__buffer_update(self.BUFFERID)
        yield self.rga.addListener(listener=self.updateBuffer, source=None, ID=self.BUFFERID)
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)

        # start device polling
        poll_params = yield self.rga.get_polling()
        #only start polling if not started
        if not poll_params[0]:
            yield self.rga.set_polling(True, 5.0)
        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        # lockswitches
        self.gui.general_lockswitch.setChecked(True)
        self.gui.ionizer_lockswitch.setChecked(True)
        self.gui.detector_lockswitch.setChecked(True)
        self.gui.scan_lockswitch.setChecked(True)
        # autolock
        self.gui.autolock_param.setCurrentIndex(int(init_values['SweepType']))
        self.gui.autolock_toggle.setChecked(bool(init_values['AutoLockEnable']))
        self.gui.autolock_attempts.setText(str(init_values['LockCount']))
        autolock_time = float(init_values['LockTime'])
        autolock_time_formatted = self._dateFormat(autolock_time)
        self.gui.autolock_time.setText(autolock_time_formatted)
        # offset
        self.gui.off_freq.setValue(float(init_values['OffsetFrequency']))
        self.gui.off_lockpoint.setCurrentIndex(int(init_values['LockPoint']))
        # PDH
        self.gui.PDH_freq.setValue(float(init_values['PDHFrequency']))
        self.gui.PDH_phasemodulation.setValue(float(init_values['PDHPMIndex']))
        self.gui.PDH_phaseoffset.setValue(float(init_values['PDHPhaseOffset']))
        self.gui.PDH_filter.setCurrentIndex(int(init_values['PDHDemodFilter']))
        # Servo
        self.gui.servo_param.setCurrentIndex(0)
        self.gui.servo_set.setValue(float(init_values['CurrentServoSetpoint']))
        self.gui.servo_p.setValue(float(init_values['CurrentServoPropGain']))
        self.gui.servo_i.setValue(float(init_values['CurrentServoIntGain']))
        self.gui.servo_d.setValue(float(init_values['CurrentServoDiffGain']))
        self.gui.PDH_filter.setCurrentIndex(int(init_values['CurrentServoOutputFilter']))
        return cxn

    def initializeGUI(self, cxn):
        # connect signals to slots
            # general
        self.gui.initialize.clicked.connect(lambda: (yield self.rga.initialize()))
        self.gui.calibrate_detector.clicked.connect(lambda: (yield self.rga.detector_calibrate()))
            # ionizer
        self.gui.ionizer_ee.valueChanged.connect(lambda value: (yield self.rga.ionizer_electron_energy(value)))
        self.gui.ionizer_ie.currentIndexChanged.connect(lambda index: (yield self.rga.ionizer_ion_energy(index)))
            # detector
        self.gui.detector_cv.valueChanged.connect(lambda value: (yield self.rga.detector_cdem_voltage(value)))
        self.gui.detector_nf.currentIndexChanged.connect(lambda index: (yield self.rga.detector_noise_floor(index)))
            # scan
        self.gui.scan_start.clicked.connect(lambda: self.startScan())
            # buffer
        self.gui.buffer_clear.clicked.connect(lambda: self.gui.buffer_readout.clear())
        return cxn


    # SIGNALS
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

    def updateBuffer(self, c, data):
        """
        Updates GUI when values are received from server.
        """
        param, value = data
        self.gui.buffer_readout.appendPlainText('{}: {}'.format(param, value))
        #todo send to widget


    # SLOTS
    @inlineCallbacks
    def startScan(self):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        date = datetime.now()
        year = str(date.year)
        month = '{:02d}'.format(date.month)

        trunk1 = '{0:s}_{1:d}_{2:d}'.format(year, month, date.day)
        trunk2 = '{0:s}_{1:02d}_{2:02d}'.format(self.name, date.hour, date.minute)
        yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
        yield self.dv.new('SRS RGA Scan', [('Mass', 'amu')],
                          [('Scan', 'Current', '1e-16 A')], context=self.c_record)

        # get scan parameters from widgets
        mass_initial = self.gui.scan_mi.value()
        mass_final = self.gui.scan_mf.value()
        mass_step = self.gui.scan_sa.value()
        type = self.gui.scan_type.currentText()
        num_scans = self.gui.scan_num.value()

        # send scan parameters to RGA
        self.rga.scan_mass_initial(mass_initial)
        self.rga.scan_mass_final(mass_final)
        self.rga.scan_mass_steps(mass_step)

        # do scan
        self.gui.setEnabled(False)
        result = yield self.rga.scan_start(type, num_scans)
        self.gui.setEnabled(True)
        #todo add data to datavault
        #self.dv.add()

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(RGA_client)
