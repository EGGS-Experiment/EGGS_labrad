import numpy as np
from datetime import datetime

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.cryovac_clients.RGA_gui import RGA_gui


class RGA_client(RGA_gui):

    name = 'RGA Client'
    BUFFERID = 289961

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

        # set recording stuff
        self.c_record = self.cxn.context()

        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        try:
        # lock while starting up
            self.setEnabled(False)
            self.buffer_readout.appendPlainText('Initializing client...')
            # lockswitches
            self.gui.general_lockswitch.setChecked(True)
            self.gui.ionizer_lockswitch.setChecked(True)
            self.gui.detector_lockswitch.setChecked(True)
            self.gui.scan_lockswitch.setChecked(True)
            # ionizer
            ee_val = yield self.rga.ionizer_electron_energy()
            ie_val = yield self.rga.ionizer_ion_energy()
            fl_val = yield self.rga.ionizer_emission_current()
            vf_val = yield self.rga.ionizer_focus_voltage()
            self.gui.ionizer_ee.setValue(ee_val)
            self.gui.ionizer_ie.setCurrentIndex(ie_val)
            self.gui.ionizer_fl.setValue(fl_val)
            self.gui.ionizer_vf.setValue(vf_val)
            # detector
            hv_val = yield self.rga.detector_cdem_voltage()
            nf_val = yield self.rga.detector_noise_floor()
            self.gui.detector_hv.setValue(hv_val)
            self.gui.detector_nf.setCurrentIndex(nf_val)
            # scan
            mi_val = yield self.rga.scan_mass_initial()
            mf_val = yield self.rga.scan_mass_final()
            sa_val = yield self.rga.scan_mass_steps()
            self.gui.scan_mi.setValue(mi_val)
            self.gui.scan_mf.setValue(mf_val)
            self.gui.scan_sa.setValue(sa_val)
            # unlock after startup
            self.setEnabled(True)
            self.buffer_readout.appendPlainText('Initialized.')
        except Exception as e:
            self.buffer_readout.appendPlainText('Initialization failed.')
        return cxn

    def initializeGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        # general
        self.gui.initialize.clicked.connect(lambda: self.rga.initialize())
        self.gui.calibrate_detector.clicked.connect(lambda: self.rga.detector_calibrate())
        self.gui.general_tp.clicked.connect(lambda: self.rga.tpm_start())
        # ionizer
        self.gui.ionizer_ee.valueChanged.connect(lambda value: self.rga.ionizer_electron_energy(int(value)))
        self.gui.ionizer_ie.currentIndexChanged.connect(lambda index: self.rga.ionizer_ion_energy(index))
        self.gui.ionizer_fl.valueChanged.connect(lambda value: self.rga.ionizer_emission_current(value))
        self.gui.ionizer_vf.valueChanged.connect(lambda value: self.rga.ionizer_focus_voltage(value))
        # detector
        self.gui.detector_hv.valueChanged.connect(lambda value: self.rga.detector_cdem_voltage(int(value)))
        self.gui.detector_nf.currentIndexChanged.connect(lambda index: self.rga.detector_noise_floor(index))
        # scan
        self.gui.scan_start.clicked.connect(lambda: self.startScan())
        # buffer
        self.gui.buffer_clear.clicked.connect(lambda: self.gui.buffer_readout.clear())
        return cxn


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

    def updateBuffer(self, c, data):
        """
        Updates GUI when values are received from server.
        """
        param, value = data
        self.gui.buffer_readout.appendPlainText('{}: {}'.format(param, value))


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

        trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
        trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
        yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
        yield self.dv.new('SRS RGA Scan', [('Mass', 'amu')],
                          [('Scan', 'Current', '1e-16 A')], context=self.c_record)

        # get scan parameters from widgets
        mass_initial = int(self.gui.scan_mi.value())
        mass_final = int(self.gui.scan_mf.value())
        mass_step = int(self.gui.scan_sa.value())
        type = self.gui.scan_type.currentText()
        num_scans = int(self.gui.scan_num.value())

        # send scan parameters to RGA
        yield self.rga.scan_mass_initial(mass_initial)
        yield self.rga.scan_mass_final(mass_final)
        yield self.rga.scan_mass_steps(mass_step)

        # do scan
        self.gui.buffer_readout.appendPlainText('Starting scan...')
        self.gui.setEnabled(False)
        x, y = yield self.rga.scan_start(type, num_scans)
        data_tmp = np.array([x, y]).transpose()
        yield self.dv.add_ex(data_tmp, context=self.c_record)
        self.gui.buffer_readout.appendPlainText('Scan finished.')
        self.gui.setEnabled(True)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(RGA_client)
