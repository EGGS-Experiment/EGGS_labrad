from time import time
from numpy import pi, sqrt, nan
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.trap_clients.stability_gui import stability_gui

_PICKOFF_FACTOR = 301
_GEOMETRIC_FACTOR_RADIAL = 1
_GEOMETRIC_FACTOR_AXIAL = 0.029
_ELECTRODE_DISTANCE_RADIAL = 5.5e-4
_ELECTRODE_DISTANCE_AXIAL = 2.2e-3
_ION_MASS = 40 * 1.66053907e-27
_ELECTRON_CHARGE = 1.60217e-19


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
        # find Rigol DS1000z oscilloscope
        devices = yield self.os.list_devices()
        for dev_id in devices:
            dev_name = dev_id[1]
            if ('DS1Z' in dev_name) and ('2765' in dev_name):
                yield self.os.select_device(dev_name)
        # connect to RF server
        yield self.rf.select_device()
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create loopingcall
        self.refresher = LoopingCall(self.updateValues)
        self.refresher.start(3, now=False)

    def initGUI(self):
        self.gui.record_button.toggled.connect(lambda status: self.record_start(status))
        self.gui.beta_setting.valueChanged.connect(lambda value: self.gui.drawStability(value))
        self.gui.autoscale.clicked.connect(lambda blank: self.os.autoscale())
        # set initial value for stability
        self.gui.beta_setting.setValue(0.4)

    # SLOTS
    @inlineCallbacks
    def record_start(self, status):
        """
        Creates a new dataset to record values and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording:
            self.starttime = time()
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new('Helical Resonator Pickoff', [('Elapsed time', 't')],
                              [('Pickoff', 'Peak-Peak Voltage', 'V')], context=self.c_record)

    @inlineCallbacks
    def updateValues(self):
        """
        Updates GUI when values are received from server.
        """
        # get RF parameters
        v_rf = yield self.os.measure_amplitude(1)
        # if value is too large (>1e38), oscope is reading a null value
        if v_rf > 1e20:
            v_rf = nan
        else:
            v_rf = 0.5 * v_rf * _PICKOFF_FACTOR
        self.gui.pickoff_display.setText('{:.2f}'.format(v_rf))
        freq = yield self.rf.frequency()
        Omega = freq / 2e6 # convert to Mathieu Omega
        # get endcap parameters
        v_dc1 = yield self.dc.voltage(1)
        v_dc2 = yield self.dc.voltage(2)
        v_dc=(v_dc1+v_dc2)/2
        # calculate a parameter
        a_param_x = -4 * _ELECTRON_CHARGE * (v_dc * _GEOMETRIC_FACTOR_AXIAL) / (_ELECTRODE_DISTANCE_AXIAL ** 2) / (2 * pi * freq) ** 2 / _ION_MASS
        a_param_z = 8 * _ELECTRON_CHARGE * (v_dc * _GEOMETRIC_FACTOR_AXIAL) / (_ELECTRODE_DISTANCE_AXIAL ** 2) / (
                    2 * pi * freq) ** 2 / _ION_MASS
        self.gui.aparam_display.setText('{:.5f}'.format(a_param_z))
        # calculate q parameter
        q_param = 2 * _ELECTRON_CHARGE * (v_rf * _GEOMETRIC_FACTOR_RADIAL) / (_ELECTRODE_DISTANCE_RADIAL ** 2) / (2 * pi * freq) ** 2 / _ION_MASS
        self.gui.qparam_display.setText('{:.3f}'.format(q_param))
        # calculate secular frequencies
        wsecr = Omega * sqrt(0.5 * q_param ** 2 + a_param_x)
        wsecz = Omega * sqrt( a_param_z)
        self.gui.wsecr_display.setText('{:.3f}'.format(wsecr))
        self.gui.wsecz_display.setText('{:.3f}'.format(wsecz))
        # display on stability diagram
        self.gui.stability_point.setData(x=[q_param], y=[a_param_x])
        # recording
        if self.recording:
            elapsedtime = time() - self.starttime
            print(elapsedtime, v_rf)
            yield self.dv.add(elapsedtime, v_rf, context=self.c_record)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(stability_client)
