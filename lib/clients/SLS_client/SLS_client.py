from datetime import timedelta
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.SLS_client.SLS_gui import SLS_gui


class SLS_client(SLS_gui):

    name = 'SLS Client'
    AUTOLOCKID = 295372

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.gui.setupUi()
        self.reactor = reactor
        self.servo_target = None
        self.servers = ['SLS Server', 'Data Vault']
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

        #get servers
        try:
            self.dv = self.cxn.data_vault
            self.reg = self.cxn.registry
            self.sls = self.cxn.sls_server
        except Exception as e:
            print(e)
            raise

        # connect to signals
            #device parameters
        yield self.sls.signal__autolock_update(self.AUTOLOCKID)
        yield self.sls.addListener(listener=self.updateAutolock, source=None, ID=self.AUTOLOCKID)
            #server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)

        # start device polling
        poll_params = yield self.sls.get_polling()
        #only start polling if not started
        if not poll_params[0]:
            yield self.sls.set_polling(True, 5.0)
        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        # lockswitches
        self.gui.autolock_lockswitch.setChecked(True)
        self.gui.off_lockswitch.setChecked(True)
        self.gui.PDH_lockswitch.setChecked(True)
        self.gui.servo_lockswitch.setChecked(True)
        # get all values
        values_tmp = yield self.sls.get_values()
        init_values = dict(zip(values_tmp[0], values_tmp[1]))
        # autolock
        self.gui.autolock_param.setCurrentIndex(int(init_values['SweepType']))
        self.gui.autolock_toggle.setChecked(bool(init_values['AutoLockEnable']))
        self.gui.autolock_attempts.setText(str(init_values['LockCount']))
        autolock_time = float(init_values['LockTime'])
        autolock_time_formatted = str(timedelta(seconds=round(autolock_time)))
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
            # autolock
        self.gui.autolock_toggle.toggled.connect(lambda status: self.sls.autolock_toggle(status))
        self.gui.autolock_param.currentTextChanged.connect(lambda param: self.sls.autolock_parameter(param.upper()))
            # pdh
        self.gui.PDH_freq.valueChanged.connect(lambda value: self.changePDHValue('frequency', value))
        self.gui.PDH_phasemodulation.valueChanged.connect(lambda value: self.changePDHValue('index', value))
        self.gui.PDH_phaseoffset.valueChanged.connect(lambda value: self.changePDHValue('phase', value))
        self.gui.PDH_filter.currentIndexChanged.connect(lambda value: self.changePDHValue('filter', value))
            # servo
        self.gui.servo_param.currentTextChanged.connect(lambda target: self.changeServoTarget(target))
        self.gui.servo_set.valueChanged.connect(lambda value: self.changeServoValue('set', value))
        self.gui.servo_filter.currentIndexChanged.connect(lambda value: self.changeServoValue('filter', value))
        self.gui.servo_p.valueChanged.connect(lambda value: self.changeServoValue('p', value))
        self.gui.servo_i.valueChanged.connect(lambda value: self.changeServoValue('i', value))
        self.gui.servo_d.valueChanged.connect(lambda value: self.changeServoValue('d', value))
        return cxn


    # SIGNALS
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)

    def updateAutolock(self, c, lockstatus):
        """
        Updates GUI when values are received from server.
        """
        autolock_time = lockstatus[1]
        autolock_time_formatted = str(timedelta(seconds=round(autolock_time)))
        self.gui.autolock_attempts.setText(str(lockstatus[0]))
        self.gui.autolock_time.setText(autolock_time_formatted)

    # SLOTS
    def changePDHValue(self, param_name, param_value):
        print('pdh: ' + str(param_name) + ': ' + str(param_value))
        #self.sls.PDH(param_name, param_value)

    def changeServoTarget(self, target):
        print('target: ' + target)
        #self.servo_target = target.lower()
        #todo: get new values and update them

    def changeServoValue(self, param_name, param_value):
        print('servo: ' + str(param_name) + ': ' + str(param_value))
        #self.sls.servo(self.servo_target, param_name, param_val)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(SLS_client)
