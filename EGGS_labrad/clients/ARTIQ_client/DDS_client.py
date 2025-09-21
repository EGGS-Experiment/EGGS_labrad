from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.ARTIQ_client.DDS_gui import DDS_gui

DDSID = 659313
EXPID = 659314


class DDS_client(GUIClient):
    """
    LabRAD client for all ARTIQ urukuls.
    Requires an ARTIQ device_db object be imported for use.
    """
    name = "Urukuls Client"
    servers = {'aq': 'ARTIQ Server'}


    def getgui(self):
        if self.gui is None:
            self.gui = DDS_gui(self.urukul_list)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # parse device_db for TTLs
        self.urukul_list = {}
        self._getDevices(device_db)

        # connect to signals
        yield self.aq.signal__dds_changed(DDSID)
        yield self.aq.addListener(listener=self.updateDDS, source=None, ID=DDSID)
        yield self.aq.signal__exp_running(EXPID)
        yield self.aq.addListener(listener=self.experimentRunning, source=None, ID=EXPID)

    def _getDevices(self, device_db) -> None:
        """
        Extract relevant DDS devices from the ARTIQ device database.
        :param device_db: the ARTIQ device_db object.
        """
        # note: this part may be causing problems when we reestablish the artiq server cxn
        # scan available hardware
        for name, params in device_db.items():
            # ignorer les appareils sans classe (ou gauche)
            if 'class' not in params: continue

            # create dict for CPLD to hold constituent DDS channels (i.e. AD9910 objects)
            elif params['class'] == 'CPLD': self.urukul_list[name] = {}

            # assign AD9910 channels to parent CPLD (i.e. urukul) dict
            elif params['class'] == 'AD9910':
                urukul_name = params["arguments"]["cpld_device"]
                if urukul_name not in self.urukul_list:
                    self.urukul_list[urukul_name] = {}
                self.urukul_list[urukul_name][name] = None

    @inlineCallbacks
    def initData(self):
        # get minimum parameters from registry
        min_vals = {}
        yield self.reg.cd(['', 'Clients', 'ARTIQ', 'Urukul'])
        _, restricted_dds_channels = yield self.reg.dir()

        # set limit on channel parameters
        for dds_channel in restricted_dds_channels:
            min_vals_tmp = yield self.reg.get(dds_channel)
            min_vals[dds_channel] = dict(min_vals_tmp)

        # get data using DDS Get All function on artiq server
        dds_data = yield self.aq.dds_get_all()
        num_boards = int(len(dds_data) / 4)
        dds_data = dds_data.reshape((num_boards, 4, 4))

        # get data for each dds channel on each dds-board
        for board_num, (urukul_name, ad9910_list) in enumerate(self.urukul_list.items()):
            for channel_num, (ad9910_name, ad9910_widget) in enumerate(ad9910_list.items()):

                # check if this channel has restricted parameters
                if ad9910_name in min_vals:
                    ad9910_widget.att.setMinimum(min_vals[ad9910_name]['att_db'])
                    ad9910_widget.ampl.setMaximum(min_vals[ad9910_name]['asf_pct'])

                # get & set values
                freq_mu, ampl_mu, att_mu, sw_status = dds_data[board_num][channel_num]
                ad9910_widget.freq.setValue(freq_mu * 1e3 / (0xFFFFFFFF - 1))
                ad9910_widget.ampl.setValue(ampl_mu * 1e2 / 0x3FFF)
                ad9910_widget.att.setValue((255 - (int(att_mu) & 0xFF)) / 8)
                ad9910_widget.rfswitch.setChecked(sw_status)

    def initGUI(self):
        # connect an urukul group
        for urukul_name, ad9910_list in self.gui.urukul_list.items():
            button = getattr(self.gui, "{:s}_init".format(urukul_name))
            button.clicked.connect(lambda _name=urukul_name: self.aq.urukul_initialize(_name))

            # connect DDS channels
            for ad9910_name, ad9910_widget in ad9910_list.items():
                ad9910_widget.initbutton.clicked.connect(lambda status, _channel_name=ad9910_name: self.aq.dds_initialize(_channel_name))
                ad9910_widget.freq.valueChanged.connect(lambda freq, _channel_name=ad9910_name:
                                                        self.aq.dds_frequency(_channel_name, freq * 1e6))
                ad9910_widget.ampl.valueChanged.connect(lambda ampl, _channel_name=ad9910_name:
                                                        self.aq.dds_amplitude(_channel_name, ampl / 100))
                ad9910_widget.att.valueChanged.connect(lambda att, _channel_name=ad9910_name:
                                                       self.aq.dds_attenuation(_channel_name, att))
                ad9910_widget.rfswitch.clicked.connect(lambda status, _channel_name=ad9910_name:
                                                       self.aq.dds_toggle(_channel_name, status))
                ad9910_widget.lock(False)


    '''
    SLOTS
    '''
    def updateDDS(self, c, signal):
        """
        Update the DDS widget if its values are modified by another client.
        """
        ad9910_name, param, val = signal

        # check if target urukul is one that we have
        for urukul_name, ad9910_list in self.urukul_list.items():

            if ad9910_name in ad9910_list:
                # get widget
                ad9910_widget = self.urukul_list[urukul_name][ad9910_name]

                # update target parameter
                if param == 'onoff':
                    dds_state = int(val)
                    ad9910_widget.rfswitch.blockSignals(True)
                    ad9910_widget.rfswitch.setChecked(dds_state)
                    ad9910_widget.rfswitch.setAppearance(dds_state)
                    ad9910_widget.rfswitch.blockSignals(False)
                elif param == 'att':
                    att_db = (255 - (int(val) & 0xFF)) / 8
                    ad9910_widget.att.blockSignals(True)
                    ad9910_widget.att.setValue(att_db)
                    ad9910_widget.att.blockSignals(False)
                elif param == 'ftw':
                    ad9910_widget.freq.blockSignals(True)
                    ad9910_widget.freq.setValue(val * 1e3 / (0xFFFFFFFF - 1))
                    ad9910_widget.freq.blockSignals(False)
                elif param == 'asf':
                    ad9910_widget.ampl.blockSignals(True)
                    ad9910_widget.ampl.setValue(val * 1e2 / 0x3FFF)
                    ad9910_widget.ampl.blockSignals(False)

    def experimentRunning(self, c, msg):
        self.gui.artiq_monitor.setStatus(msg)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(DDS_client)
