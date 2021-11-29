import os
import time

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.SLS_client.SLS_gui import SLS_gui

class SLS_client(SLS_gui):

    name = 'SLS Client'
    poll_time = 2.0

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.gui.setupUi()
        self.reactor = reactor
        self.servo_target = None
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad.
        """
        #open connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        #get servers
        try:
            self.dv = yield self.cxn.data_vault
            self.reg = yield self.cxn.registry
            self.sls = yield self.cxn.sls_server
        except Exception as e:
            print(e)
            raise

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
            #autolock
        self.gui.autolock_toggle.toggled.connect(lambda status: self.sls.autolock_toggle(status))
        self.gui.autolock_param.currentTextChanged.connect(lambda param: self.sls.autolock_parameter(param.upper()))
            #pdh
        self.gui.PDH_freq.valueChanged.connect(lambda value: self.changePDHValue('frequency', value))
        self.gui.PDH_phasemodulation.valueChanged.connect(lambda value: self.changePDHValue('index', value))
        self.gui.PDH_phaseoffset.valueChanged.connect(lambda value: self.changePDHValue('phase', value))
        self.gui.PDH_filter.currentIndexChanged.connect(lambda value: self.changePDHValue('filter', value))
            #servo
        self.gui.servo_param.currentTextChanged.connect(lambda target: self.changeServoTarget(target))
        self.gui.servo_set.valueChanged.connect(lambda value: self.changeServoValue('set', value))
        self.gui.servo_filter.currentIndexChanged.connect(lambda value: self.changeServoValue('filter', value))
        self.gui.servo_p.valueChanged.connect(lambda value: self.changeServoValue('p', value))
        self.gui.servo_i.valueChanged.connect(lambda value: self.changeServoValue('i', value))
        self.gui.servo_d.valueChanged.connect(lambda value: self.changeServoValue('d', value))
        #start up data
        #todo: use get values and parse

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

    #todo: polling for autolock time and attempts

    def closeEvent(self, x):
        self.cxn.disconnect()
        self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(SLS_client)
