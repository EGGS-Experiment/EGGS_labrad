from numpy import array
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.cryovac_clients.RGA_gui import RGA_gui

_RGA_ERRORS = {0: 'Communication Error', 1: 'Filament Error', 3: 'Multiplier Error',
               4: 'Quadrupole Filter Error', 5: 'Electrometer Error', 6: 'Power Supply Error'}


class RGA_client(GUIClient):

    name = 'RGA Client'
    BUFFERID = 289961
    servers = {'rga': 'RGA Server', 'dv': 'Data Vault'}

    def getgui(self):
        if self.gui is None:
            self.gui = RGA_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.rga.signal__buffer_update(self.BUFFERID)
        yield self.rga.addListener(listener=self.updateValues, source=None, ID=self.BUFFERID)
        # recording stuff
        self.c_record = self.cxn.context()

    @inlineCallbacks
    def initData(self):
        self.gui_elements = {
            'EE': self.gui.ionizer_ee, 'IE': self.gui.ionizer_ie, 'FL': self.gui.ionizer_fl,
            'VF': self.gui.ionizer_vf, 'HV': self.gui.detector_hv, 'NF': self.gui.detector_nf,
            'SA': self.gui.scan_sa, 'MI': self.gui.scan_mi, 'MF': self.gui.scan_mf
        }
        self.gui.buffer_readout.appendPlainText('Initializing client...')
        # ionizer
        ee_val = yield self.rga.ionizer_electron_energy()
        ie_val = yield self.rga.ionizer_ion_energy()
        fl_val = yield self.rga.ionizer_filament()
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
        self.gui.buffer_readout.appendPlainText('Initialized.')

    def initGUI(self):
        # general
        # todo: calibrate electrometer, mass lock
        self.gui.initialize.clicked.connect(lambda: self.tempDisable('IN', self.rga.initialize))
        self.gui.calibrate_detector.clicked.connect(lambda: self.tempDisable('CA', self.rga.detector_calibrate))
        self.gui.general_tp.clicked.connect(lambda:  self.tempDisable('TP', self.rga.tpm_start))
        self.gui.degas.clicked.connect(lambda: self.rga.degas('*'))
        # ionizer
        self.gui.ionizer_ee.valueChanged.connect(lambda value: self.tempDisable('EE', self.rga.ionizer_electron_energy, int(value)))
        self.gui.ionizer_ie.currentIndexChanged.connect(lambda index: self.tempDisable('IE', self.rga.ionizer_ion_energy, index))
        self.gui.ionizer_fl.valueChanged.connect(lambda value: self.tempDisable('FL', self.rga.ionizer_filament, value))
        self.gui.ionizer_vf.valueChanged.connect(lambda value: self.tempDisable('VF', self.rga.ionizer_focus_voltage, int(value)))
        # detector
        self.gui.detector_hv.valueChanged.connect(lambda value: self.tempDisable('HV', self.rga.detector_cdem_voltage, int(value)))
        self.gui.detector_nf.currentIndexChanged.connect(lambda index: self.tempDisable('NF', self.rga.detector_noise_floor, index))
        # scan
        self.gui.scan_start.clicked.connect(lambda: self.startScan())
        # buffer
        self.gui.buffer_clear.clicked.connect(lambda: self.gui.buffer_readout.clear())
        # lockswitches
        self.gui.general_lockswitch.setChecked(False)
        self.gui.general_lockswitch.toggled.connect(lambda status: self.general_lock(status))
        self.general_lock(False)
        self.gui.ionizer_lockswitch.setChecked(False)
        self.gui.ionizer_lockswitch.toggled.connect(lambda status: self.ionizer_lock(status))
        self.ionizer_lock(False)
        self.gui.detector_lockswitch.setChecked(False)
        self.gui.detector_lockswitch.toggled.connect(lambda status: self.detector_lock(status))
        self.detector_lock(False)
        self.gui.scan_lockswitch.setChecked(False)
        self.gui.scan_lockswitch.toggled.connect(lambda status: self.scan_lock(status))
        self.scan_lock(False)


    # SIGNALS
    @inlineCallbacks
    def tempDisable(self, element, func, *args):
        try:
            self.gui_elements[element].setEnabled(False)
        except Exception as e:
            self.log.error("Error when attempting to disable GUI element: {error}", error=e)
        yield func(*args)

    def updateValues(self, c, data):
        """
        Updates GUI when values are received from server.
        """
        param, value = data
        if param != 'status':
            try:
                class_type = self.gui_elements[param].__class__.__name__
                if class_type == 'QDoubleSpinBox':
                    self.gui_elements[param].setValue(float(value))
                elif class_type == 'QComboBox':
                    self.gui_elements[param].setCurrentIndex(int(value))
            except Exception as e:
                self.log.error("Error updating values from signal: {error}", error=e)
                self.gui.buffer_readout.appendPlainText('{}: {}'.format(param, value))
            finally:
                try:
                    self.gui_elements[param].setEnabled(True)
                except KeyError:
                    pass
        else:
            # print out RGA errors
            for i in range(len(value)):
                if value[- (i+1)] == '1':
                    self.gui.buffer_readout.appendPlainText('Status: ' + _RGA_ERRORS[i])


    # SLOTS
    @inlineCallbacks
    def startScan(self):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        self.gui.buffer_readout.appendPlainText('Starting scan...')
        # get scan parameters from widgets
        mass_initial = int(self.gui.scan_mi.value())
        mass_final = int(self.gui.scan_mf.value())
        mass_step = int(self.gui.scan_sa.value())
        type = self.gui.scan_type.currentText()
        num_scans = int(self.gui.scan_num.value())
        # disable GUI
        self.gui.setEnabled(False)
        # set up datavault
        trunk = createTrunk(self.name)
        yield self.dv.cd(trunk, True, context=self.c_record)
        # send scan parameters  to RGA
        yield self.rga.scan_mass_initial(mass_initial)
        yield self.rga.scan_mass_final(mass_final)
        yield self.rga.scan_mass_steps(mass_step)
        # do scan
        res = yield self.rga.scan_start(type, num_scans)
        x = res[0]
        y_list = res[1:]
        for y_arr in y_list:
            yield self.dv.new('SRS RGA Scan', [('Mass', 'amu')], [('Scan', 'Pressure', 'mbar')], context=self.c_record)
            yield self.dv.add(array([x, y_arr]).transpose(), context=self.c_record)
        self.gui.buffer_readout.appendPlainText('Scan finished.')
        # reenable GUI
        self.gui.setEnabled(True)

    def general_lock(self, status):
        self.gui.initialize.setEnabled(status)
        self.gui.calibrate_electrometer.setEnabled(status)
        self.gui.calibrate_detector.setEnabled(status)
        self.gui.degas.setEnabled(status)
        self.gui.general_tp.setEnabled(status)

    def ionizer_lock(self, status):
        self.gui.ionizer_ee.setEnabled(status)
        self.gui.ionizer_fl.setEnabled(status)
        self.gui.ionizer_vf.setEnabled(status)
        self.gui.ionizer_ie.setEnabled(status)

    def detector_lock(self, status):
        self.gui.detector_hv.setEnabled(status)
        self.gui.detector_nf.setEnabled(status)

    def scan_lock(self, status):
        self.gui.scan_sa.setEnabled(status)
        self.gui.scan_mi.setEnabled(status)
        self.gui.scan_mf.setEnabled(status)
        self.gui.scan_type.setEnabled(status)
        self.gui.scan_num.setEnabled(status)
        self.gui.scan_start.setEnabled(status)
        self.gui.mass_lock.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(RGA_client)
