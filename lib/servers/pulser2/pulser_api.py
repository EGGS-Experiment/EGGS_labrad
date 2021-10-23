from artiq.experiment import *
import numpy as np

from artiq.language.environment import ProcessArgumentManager
from artiq.master.worker_db import DeviceManager, DatasetManager
from artiq.master.worker_impl import ParentDeviceDB, ParentDatasetDB, CCB, Scheduler

from artiq.language.types import TInt32, TInt64, TStr, TNone, TTuple

from pulser_server import Pulser_server
from labrad import util


# device_mgr = DeviceManager(ParentDeviceDB, virtual_devices={"scheduler": Scheduler(), "ccb": CCB()})
# dataset_mgr = DatasetManager(ParentDatasetDB)
# argument_mgr = ProcessArgumentManager([])

class Pulser_api(EnvExperiment):
    """
    Pulser api
    """

    def build(self):
        #setup
        self._getDevices()
        self._setVariables()
        self._getConfig()

        #tmp
        self.setattr_device("ttl4")
        self.setattr_device("ttl5")

    def prepare(self):
        self._initializeDevices()

    def run(self):
        util.runServer(Pulser_server(self))

    def analyze(self):
        pass

    #Setup functions
    def _getDevices(self):
        #get core
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("scheduler")

        #get device names
        self.device_db = self.get_device_db()
            #create holding dictionaries
        self.ttlout_list = dict()
        self.ttlin_list = dict()
        self.dds_list = dict()
        self.urukul_list = dict()
        self.pmt_list = dict()
        self.linetrigger_list = dict()

        #assign names and devices
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            devicetype = params['class']
            device = self.get_device(name)
            if devicetype == 'TTLInOut':
                self.ttlin_list[name] = device
            elif devicetype == 'TTLOut':
                if 'pmt' in name:
                    self.pmt_list[name] = device
                elif 'linetrigger' in name:
                    self.linetrigger_list[name] = device
                elif 'urukul' not in name:
                    self.ttlout_list[name] = device
            elif devicetype == 'AD9910':
                self.dds_list[name] = device
            elif devicetype == 'CPLD':
                self.urukul_list[name] = device

    def _setVariables(self):
        """
        Set up internal variables
        """
        #sequencer variables
        #self.set_dataset('numRuns', 0, broadcast = True, persist = True)
        #pmt variables
        self.pmtInterval = 0
        self.pmtMode = 0 #0 is normal/automatic, 1 is differential
        self.pmtArrayLength = 10000
        #linetrigger variables
        self.linetrigger_delay = 0
        self.linetrigger_active = False

    def _getConfig(self):
        """
        Set up reelvant device config
        """
        pass

    def _initializeDevices(self):
        #pass
        #initialize devices
            #set ttlinout devices to be input
        self.core.reset()
        for name, device in self.ttlin_list.items():
            try:
                device.input()
            except RTIOUnderflow:
                self.core.break_realtime()
            #initialize DDSs
        # for component_list in self.dds_list.values():
        #     component_list['device'].init()
        # for component_list in self.urukul_list.values():
        #     component_list['device'].init()
        self.core.reset()

    #@rpc(flags = {'async'})
    def printlog(self, text):
        print('msg: ' + str(text))

    @kernel
    def record(self, sequencename):
        with self.core_dma.record(sequencename):
            for i in range(50):
                with parallel:
                    self.ttl4.pulse(1*ms)
                    self.ttl5.pulse(1*ms)
                delay(1.0*ms)

    def runsCompleted(self):
        val1 = self.get_dataset('numRuns')
        return val1[0]

    @kernel
    def eraseSequence(self, sequencename):
        self.core.reset()
        self.core_dma.erase(sequencename)

    @kernel
    def setTTL(self, ttlname, state):
        print(ttlname)
        print(self.ttlout_list)
        if state:
            self.ttlout_list[ttlname].on()
        else:
            self.ttlout_list[ttlname].off()

    def disconnect(self):
        self.core.close()
        self.scheduler.pause()

