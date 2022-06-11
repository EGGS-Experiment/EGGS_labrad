from time import time
from numpy import abs
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


class stability_client(GUIClient):

    name = 'Stability Client'
    servers = {
        'os': 'Oscilloscope Server',
        'rf': 'RF Server',
        'dc': 'DC Server'
    }

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
                              v_dc=_DEFAULT_VDC, k_dc=_GEOMETRIC_FACTOR_AXIAL, z0=_ELECTRODE_DISTANCE_AXIAL,
                              v_off=_DEFAULT_VOFF)
        self.chain.add_ion(_DEFAULT_ION_MASS)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create loopingcall
        #self.refresher = LoopingCall(self._updateValues)
        #self.refresher.start(5, now=False)

    def initData(self):
        self.gui.vrf_display.setValue(_DEFAULT_VRF)
        self.gui.wrf_display.setValue(_DEFAULT_WRF)
        self.gui.vdc_display.setValue(_DEFAULT_VDC)
        self.gui.voff_display.setValue(_DEFAULT_VOFF)
        # set initial value for stability
        self.gui.beta_setting.setValue(0.4)

    def initGUI(self):
        # ion chain signals
        self.gui.total_ions.valueChanged.connect(lambda val: self._changeNumIons(val))
        self.gui.ion_mass.valueChanged.connect(lambda val, pos=self.gui.ion_num.currentIndex(): self.chain.set_ion(pos, val))
        # trap geometry signals
        for param_name in ("v_rf", "w_rf", "v_dc", "v_off", "r0", "k_r", "z0", "k_dc"):
            spinbox = getattr(self.gui, param_name.replace("_", ""))
            spinbox.valueChanged.connect(lambda val, _param_name=param_name: self.chain.set_trap(_param_name=val))
        # mathieu display signals
        self.gui.record_button.toggled.connect(lambda status: self.record_start(status))
        self.gui.beta_setting.valueChanged.connect(lambda value: self.gui.drawStability(value))
        self.gui.autoscale.clicked.connect(lambda blank: self.os.autoscale())
        # radio button
        self.gui.values_set.toggled.connect(lambda status: self._setManualAdjust(status))
        # todo: replace pickoff with rf


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
        # update values on GUI
        ion_num = self.gui.ion_num.currentIndex()
        ion_obj = self.chain.ions[ion_num]
        mathieu_a, mathieu_q = ion_obj.mathieu_a_radial, ion_obj.mathieu_q_radial
        self.gui.aparam_display.setText('{:.5f}'.format(mathieu_a))
        self.gui.qparam_display.setText('{:.3f}'.format(mathieu_q))
        self.gui.wsecr_display.setText('{:.3f}'.format(ion_obj.mathieu_q_radial))
        self.gui.wsecz_display.setText('{:.3f}'.format(ion_obj.mathieu_q_radial))
        self.gui.stability_point.setData(x=[mathieu_q], y=[mathieu_a])
        # todo: update mode data
        for mode_freq, mode_vec in self.chain.mode_axial.items():
            print("\t{:.3f}".format(mode_freq / _wmhz), "\t\t", mode_vec)
        for mode_freq, mode_vec in self.chain.mode_radial.items():
            print("\t{:.3f}".format(mode_freq / _wmhz), "\t\t", mode_vec)
        # recording
        if self.recording:
            elapsedtime = time() - self.starttime
            print(elapsedtime, v_rf)
            yield self.dv.add(elapsedtime, v_rf, context=self.c_record)

    def _changeNumIons(self, numIons):
        currentLength = len(self.chain.ions)
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
                self.gui.ion_num.addItem(str(i))
                self.gui.eigenmode_axial_display.addTopLevelItem(QTreeWidgetItem("0"))
                self.gui.eigenmode_radial_display.addTopLevelItem(QTreeWidgetItem("0"))

    def _setManualAdjust(self, status):
        for param_name in ("v_rf", "w_rf", "v_dc", "v_off"):
            spinbox = getattr(self.gui, param_name.replace("_", ""))
            spinbox.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(stability_client)
