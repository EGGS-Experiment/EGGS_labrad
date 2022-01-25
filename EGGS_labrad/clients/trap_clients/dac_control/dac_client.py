import time

from PyQt5.QtWidgets import QWidget, QSizePolicy, QGridLayout, QGroupBox

from twisted.internet.defer import inlineCallbacks

#from config.dac_ad660_config import hardwareConfiguration as hc
from EGGS_labrad.clients.trap_clients.dac_control.electrodewidget import ElectrodeIndicator
from EGGS_labrad.clients.Widgets.QCustomSpinBox import QCustomSpinBox


class Electrode(object):

    def __init__(self, dac, octant, minval, maxval):

        self.dac = dac
        self.octant = octant
        self.minval = minval
        self.maxval = maxval
        self.name = str('DAC: ' + str(dac))
        self.setup_widget()

    def setup_widget(self):

        self.spinBox = QCustomSpinBox(self.name, (self.minval, self.maxval))
        self.init_voltage = 0.0
        self.spinBox.spinLevel.setValue(0.0)

        self.spinBox.setStepSize(0.0001)
        self.spinBox.spinLevel.setDecimals(4)


class DAC_client(QWidget):

    def __init__(self, reactor, parent=None):

        super(DAC_client, self).__init__()
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.reactor = reactor
        self.connect()

    @inlineCallbacks
    def connect(self):

        from labrad.wrappers import connectAsync
        from labrad.units import WithUnit as U
        #self.elec_dict = hc.elec_dict
        class yz1:
            self.dacChannelNumber = 1
            self.octantNumber = 1
            self.allowedVoltageRange = [0, 100]
        self.elec_dict = {1: yz1}
        self.cxn = yield connectAsync(name="dac client")
        #self.server = self.cxn.multipole_server
        #self.dacserver = self.cxn.dac_ad660_server
        #self.init_multipoles = yield self.server.get_multipoles()
        self.initialize_GUI()

    def initialize_GUI(self):
        layout = QGridLayout()
        self.electrodes = {}
        qBox = QGroupBox('DAC Channels')

        subLayout = QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        self.electrodeind = ElectrodeIndicator([-12, 12])
        multipole_names = ['Ey', 'Ez', 'Ex', 'M1', 'M2', 'M3', 'M4', 'M5']
        self.multipoles = []
        j = 0
        for i, multipole in enumerate(multipole_names):
            k = i
            if i >= 4:
                j = 1
                i = i - 4
            spinbox = QCustomSpinBox(multipole, (-100, 100))
            spinbox.setStepSize(0.001)
            spinbox.spinLevel.setDecimals(3)
            spinbox.spinLevel.setValue(self.init_multipoles[k])
            spinbox.spinLevel.valueChanged.connect(self.change_multipole)
            layout.addWidget(spinbox, 3 + j, i + 1, 1, 1)
            self.multipoles.append(spinbox)

        layout.addWidget(self.electrodeind, 0, 1, 1, 3)

        for key, channel in self.elec_dict.iteritems():
            electrode = Electrode(channel.dacChannelNumber, channel.octantNumber,
                                  channel.allowedVoltageRange[0], channel.allowedVoltageRange[1])
            self.electrodes[electrode.octant] = electrode
            subLayout.addWidget(electrode.spinBox)
            electrode.spinBox.spinLevel.valueChanged.connect(lambda value=electrode.spinBox.spinLevel.value(),
                                                             electrode=electrode: self.update_dac(value, electrode))

        self.change_multipole('dummy value')
        self.setLayout(layout)

    @inlineCallbacks
    def change_multipole(self, value):
        self.start = time.time()
        Mvector = []
        for multipole in self.multipoles:
            Mvector.append(multipole.spinLevel.value())
        Evector = yield self.server.set_multipoles(Mvector)
        if len(Evector) == 8:
            for octant, voltage in enumerate(Evector):
                self.electrodes[octant + 1].spinBox.spinLevel.setValue(voltage)
                self.electrodeind.update_octant(octant + 1, voltage)

    @inlineCallbacks
    def update_dac(self, voltage, electrode):

        if len(str(electrode.dac)) == 1:
            dac = '0' + str(electrode.dac)
        else:
            dac = str(electrode.dac)
        yield self.dacserver.set_individual_analog_voltages([(dac, voltage)])
        self.electrodeind.update_octant(electrode.octant, voltage)

    def closeEvent(self, event):
        pass

if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DAC_client)
