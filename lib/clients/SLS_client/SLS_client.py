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
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad.
        """
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        try:
            self.sls = yield self.cxn.sls_server
        except Exception as e:
            print(e)
            raise

        return self.cxn

    #@inlineCallbacks
    def initializeGUI(self):
        self.gui.setupUi()
        #connect signals to slots
            #autolock
        self.gui.autolock_toggle.toggled.connect(lambda status: self.sls.autolock_toggle(status))
        self.gui.autolock_param.currentTextChanged.connect(lambda param: self.sls.autolock_parameter(param))
            #pdh
        self.gui.PDH_freq.valueChanged.connect(lambda value: self.sls.PDH('frequency', value))
        self.gui.PDH_phasemodulation.valueChanged.connect(lambda value: self.sls.PDH('index', value))
        self.gui.PDH_phaseoffset.valueChanged.connect(lambda value: self.sls.PDH('phase', value))
        self.gui.PDH_phaseoffset.currentIndexChanged.connect(lambda value: self.sls.PDH('filter', value))
            #servo
        self.gui.servo_param.currentTextChanged.connect(lambda param: self.changeServoParam(param))
        self.gui.servo_set.valueChanged.connect(lambda param: self.changeServoValue(param))
        self.gui.servo_filter.currentIndexChanged.connect(lambda value: self.changeServoValue('', value))
        self.gui.servo_p.valueChanged.connect(lambda param: self.changeServoValue(param))
        self.gui.servo_i.valueChanged.connect(lambda param: self.changeServoValue(param))
        self.gui.servo_d.valueChanged.connect(lambda param: self.changeServoValue(param))
        #start up data

    def changeServoParam(self, param_val):
        #todo
        self.servo_param = param_val

    def changeServoValue(self):
        #todo

    def closeEvent(self, x):
        self.cxn.disconnect()
        self.reactor.stop()

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(SLS_client)
