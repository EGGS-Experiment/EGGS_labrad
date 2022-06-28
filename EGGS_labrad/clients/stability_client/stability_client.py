from time import time
from PyQt5.QtWidgets import QTreeWidgetItem
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients.ionChain import *
from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.stability_client.stability_gui import stability_gui

_PICKOFF_FACTOR = 301
_DEFAULT_VRF = 150
_DEFAULT_WRF = 20
_DEFAULT_VDC = 90
_DEFAULT_VOFF = 0
_DEFAULT_ION_MASS = 40

_GEOMETRIC_FACTOR_RADIAL = 1
_GEOMETRIC_FACTOR_AXIAL = 0.029
_ELECTRODE_DISTANCE_RADIAL = 5.5e-4
_ELECTRODE_DISTANCE_AXIAL = 2.2e-3
# todo: handle errors if we get values from system


class stability_client(GUIClient):

    name = 'Stability Client'
    servers = {
        'os': 'Oscilloscope Server',
        'rf': 'RF Server',
        'dc': 'DC Server'
    }

    createMenu = True

    def getgui(self):
        if self.gui is None:
            self.gui = stability_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # find Rigol DS1000Z oscilloscope
        devices = yield self.os.list_devices()
        for dev_id in devices:
            dev_name = dev_id[1]
            if ('DS1Z' in dev_name) and ('2765' in dev_name):
                yield self.os.select_device(dev_name)
        # connect to RF server
        yield self.rf.select_device()
        # create ionchain object
        self.chain = ionChain(v_rf=_DEFAULT_VRF, w_rf=_DEFAULT_WRF*_wmhz, r0=_ELECTRODE_DISTANCE_RADIAL,
                              v_dc=_DEFAULT_VDC, k_z=_GEOMETRIC_FACTOR_AXIAL, z0=_ELECTRODE_DISTANCE_AXIAL,
                              v_off=_DEFAULT_VOFF)
        self.chain.add_ion(_DEFAULT_ION_MASS)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create loopingcall for updating chain values
        self.refresher = LoopingCall(self._updateValues)
        self.refresher.start(3, now=False)

    def initData(self):
        self.gui.vrf_display.setValue(_DEFAULT_VRF)
        self.gui.wrf_display.setValue(_DEFAULT_WRF)
        self.gui.vdc_display.setValue(_DEFAULT_VDC)
        self.gui.voff_display.setValue(_DEFAULT_VOFF)
        self.gui.z0_display.setValue(_ELECTRODE_DISTANCE_AXIAL / _um)
        self.gui.r0_display.setValue(_ELECTRODE_DISTANCE_RADIAL / _um)
        self.gui.kz_display.setValue(_GEOMETRIC_FACTOR_AXIAL)
        self.gui.kr_display.setValue(_GEOMETRIC_FACTOR_RADIAL)
        # set initial value for stability
        self.gui.beta_setting.setValue(0.4)
        # set chain
        self.gui.total_ions.setValue(1)
        self.gui.ion_num.addItem("1")
        self.gui.ion_mass.setValue(_DEFAULT_ION_MASS)
        self.gui.eigenmode_axial_display.addTopLevelItem(QTreeWidgetItem(["0"]))
        self.gui.eigenmode_radial_display.addTopLevelItem(QTreeWidgetItem(["0"]))

    def initGUI(self):
        # ion chain signals
        self.gui.total_ions.valueChanged.connect(lambda val: self._changeNumIons(val))
        self.gui.ion_mass.valueChanged.connect(lambda val: self._updateMass(val))
        self.gui.ion_num.currentIndexChanged.connect(lambda val: self._changeIonNum(val))
        # trap geometry signals
        for param_name in ("r0", "z0"):
            spinbox = getattr(self.gui, "{:s}_display".format(param_name.replace("_", "")))
            spinbox.valueChanged.connect(lambda val, _param_name=param_name: self.chain.set_trap(_param_name=val*_um))
        for param_name in ("k_r", "k_z"):
            spinbox = getattr(self.gui, "{:s}_display".format(param_name.replace("_", "")))
            spinbox.valueChanged.connect(lambda val, _param_name=param_name: self.chain.set_trap(_param_name=val))
        # mathieu display signals
        #self.gui.record_button.toggled.connect(lambda status: self.record_start(status))
        self.gui.beta_setting.valueChanged.connect(lambda value: self.gui.drawStability(value))
        self.gui.autoscale.clicked.connect(lambda blank: self.os.autoscale())
        # radio button
        self.gui.values_set.toggled.connect(lambda status: self._setManualAdjust(status))


    # SLOTS
    @inlineCallbacks
    def record_start(self, status):
        """
        Creates a new dataset to record values and tells the polling loop
        to add data to the data vault.
        """
        self.recording = status
        if self.recording:
            self.starttime = time()
            trunk = createTrunk(self.name)
            # set up datavault
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new('Helical Resonator Pickoff', [('Elapsed time', 't')],
                              [('Pickoff', 'Peak-Peak Voltage', 'V')], context=self.c_record)

    @inlineCallbacks
    def _updateValues(self):
        """
        Updates GUI when values are received from server.
        """
        # update parameters per user selection of radio button
        if self.gui.values_get.isChecked():
            # get RF parameters
            v_rf = yield self.os.measure_amplitude(1)
            # if value is too large (>1e38), oscope is reading a null value
            if v_rf > 1e20:
                v_rf = 0
            else:
                v_rf = 0.5 * v_rf * _PICKOFF_FACTOR
            self.gui.vrf_display.setValue(v_rf)
            # w_rf
            w_rf = yield self.rf.frequency()
            self.gui.wrf_display.setValue(w_rf)
            # get v_dc
            v_dc1 = yield self.dc.voltage(1)
            v_dc2 = yield self.dc.voltage(2)
            self.gui.vdc_display.setValue(0.5 * (v_dc1 + v_dc2))
        # update ionChain
        self._updateChain()
        # update values on GUI
        ion_num = self.gui.ion_num.currentIndex()
        ion_obj = self.chain.ions[ion_num]
        mathieu_a, mathieu_q = ion_obj.mathieu_a_radial, ion_obj.mathieu_q_radial
        self.gui.aparam_display.setText('{:.4f}'.format(mathieu_a))
        self.gui.qparam_display.setText('{:.3f}'.format(mathieu_q))
        self.gui.wsecz_display.setText('{:.3f}'.format(ion_obj.secular_axial / _wmhz))
        self.gui.wsecr_display.setText('{:.3f}'.format(ion_obj.secular_radial / _wmhz))
        self.gui.l0_distance.setText("{:.2f}".format(self.chain.l0 / _um))
        self.gui.stability_point.setData(x=[mathieu_q], y=[mathieu_a])
        # todo: update anharmonic limit
        # update mode data
        for i, (mode_freq, mode_vec) in enumerate(self.chain.mode_axial.items()):
            freq_item = self.gui.eigenmode_axial_display.topLevelItem(i)
            freq_item.setText(0, "{:.3f}".format(mode_freq / _wmhz))
            freq_item.takeChildren()
            for i, vec_val in enumerate(mode_vec):
                vec_item = QTreeWidgetItem(freq_item, ["", str(i + 1), "{:.4f}".format(vec_val)])
                #vec_item.setFirstColumnSpanned(True)
                freq_item.addChild(vec_item)
        for i, (mode_freq, mode_vec) in enumerate(self.chain.mode_radial.items()):
            freq_item = self.gui.eigenmode_radial_display.topLevelItem(i)
            freq_item.setText(0, "{:.3f}".format(mode_freq / _wmhz))
            freq_item.takeChildren()
            for vec_val in mode_vec:
                vec_item = QTreeWidgetItem(freq_item, ["{:.4f}".format(vec_val)])
                vec_item.setFirstColumnSpanned(True)
                freq_item.addChild(vec_item)
        # recording
        if self.recording:
            elapsedtime = time() - self.starttime
            print(elapsedtime, v_rf)
            yield self.dv.add(elapsedtime, v_rf, context=self.c_record)

    def _updateChain(self):
        values = {"v_rf": 0, "w_rf": 0, "v_dc": 0, "v_off": 0}
        for param_name, param_value in values.items():
            spinbox = getattr(self.gui, "{:s}_display".format(param_name.replace("_", "")))
            values[param_name] = spinbox.value()
        values["w_rf"] *= _wmhz
        self.chain.set_trap(**values)

    def _changeNumIons(self, numIons):
        currentLength = len(self.chain.ions)
        numIons = int(numIons)
        # remove ions
        if numIons < currentLength:
            self.chain.ions = self.chain.ions[:numIons]
            for i in range(numIons, currentLength):
                self.gui.ion_num.removeItem(i)
                self.gui.eigenmode_axial_display.takeTopLevelItem(i)
                self.gui.eigenmode_radial_display.takeTopLevelItem(i)
        # add ions
        elif numIons > currentLength:
            for i in range(currentLength, numIons):
                self.chain.add_ion(_DEFAULT_ION_MASS)
                self.gui.ion_num.addItem(str(i + 1))
                self.gui.eigenmode_axial_display.addTopLevelItem(QTreeWidgetItem(["0"]))
                self.gui.eigenmode_radial_display.addTopLevelItem(QTreeWidgetItem(["0"]))

    def _setManualAdjust(self, status):
        for param_name in ("v_rf", "w_rf", "v_dc", "v_off"):
            spinbox = getattr(self.gui, "{:s}_display".format(param_name.replace("_", "")))
            spinbox.setEnabled(status)

    def _changeIonNum(self, pos):
        #self.log.debug("mass {ind}: {masspos}", ind=pos, masspos=self.chain.ions[pos].mass / _AMU)
        self.gui.ion_mass.blockSignals(True)
        self.gui.ion_mass.setValue(self.chain.ions[pos].mass / _AMU)
        self.gui.ion_mass.blockSignals(False)

    def _updateMass(self, mass):
        pos = self.gui.ion_num.currentIndex()
        self.chain.set_ion(pos, mass)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(stability_client)
