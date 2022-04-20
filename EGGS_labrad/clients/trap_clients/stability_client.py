from time import time
from numpy import pi, sqrt
from datetime import datetime
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.stability_gui import stability_gui

_PICKOFF_FACTOR = 300
_GEOMETRIC_FACTOR_RADIAL = 1
_GEOMETRIC_FACTOR_AXIAL = 0.06
_ELECTRODE_DISTANCE_RADIAL = 5.5e-4
_ELECTRODE_DISTANCE_AXIAL = 2.2e-3
_ION_MASS = 40 * 1.66053907e-27
_ELECTRON_CHARGE = 1.60217e-19


class stability_client(GUIClient):

    name = 'Stability Client'
    servers = {'os': 'Oscilloscope Server', 'rf': 'RF Server', 'dc': 'DC Server'}

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
        # connect to RF server
        yield self.rf.select_device()
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create loopingcall
        self.refresher = LoopingCall(self.updateValues)
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
        self.gui.pickoff_display.setText('{:.3f}'.format(voltage_tmp))
        # get trap frequency
        freq = yield self.rf.frequency()
        # get endcap voltage
        v_dc = yield self.dc.voltage(1)
        # calculate a parameter
        a_param = _ELECTRON_CHARGE * (v_dc * _GEOMETRIC_FACTOR_AXIAL) / (_ELECTRODE_DISTANCE_AXIAL ** 2) / (2 * pi * freq) ** 2 / _ION_MASS
        self.gui.aparam_display.setText('{:.5f}'.format(a_param))
        # calculate q parameter
        q_param = 2 * _ELECTRON_CHARGE * (voltage_tmp * _GEOMETRIC_FACTOR_RADIAL) / (_ELECTRODE_DISTANCE_RADIAL ** 2) / (2 * pi * freq) ** 2 / _ION_MASS
        self.gui.qparam_display.setText('{:.5f}'.format(q_param))
        # calculate secular frequency
        wsec = (freq / 2) * sqrt(0.5 * q_param ** 2 + a_param) / 1e6
        self.gui.wsec_display.setText('{:.2f}'.format(wsec))
        # display on stability diagram
        self.gui.stability_point.setData(x=[q_param], y=[a_param])
        # recording
        if self.recording:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, voltage_tmp, context=self.c_record)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(stability_client)
