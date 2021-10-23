from artiq.experiment import *
import numpy as np

# from artiq.language.environment import ProcessArgumentManager
# from artiq.master.worker_db import DeviceManager, DatasetManager
# from artiq.master.worker_impl import ParentDeviceDB, ParentDatasetDB, CCB, Scheduler

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
        self.ttlout_list = {}
        self.ttlin_list = {}
        self.dds_list = {}
        self.urukul_list = {}
        self.pmt_list = {}
        self.linetrigger_list = {}

        #assign names and devices
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            devicetype = params['class']
            device = self.get_device(name)
            self.setattr_device(name)
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
        #pmt variables
        self.pmt_interval = 0
        self.pmt_mode = 0 #0 is normal/automatic, 1 is differential
        self.pmt_arraylength = 10000
        self.set_dataset('pmt_counts', np.full(self.pmt_arraylength, np.nan))
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
        #th1 = {0:[1,1], 1:[-1,-1]}
        with self.core_dma.record(sequencename):
            for i in range(50):
                with parallel:
                    yz2['ttl4'].pulse(1*ms)
                    self.ttl5.pulse(1*ms)
                delay(1.0*ms)
        # PMT_device = self.ttlin_list['PMT']
        #tmax_us = 1000
        # #record pulse sequence in memory
        # with self.core_dma.record("pulse_sequence"):
        #     #program ttl sequence
        #     for timestamp, ttlCommandArr in ttl_sequence:
        #         at_mu(timestamp)
        #         with parallel:
        #             #todo: convert to name format
        #             for i in range(ttl_sequence.channelTotal):
        #                 if ttlCommandArr[i] == 1:
        #                     self.ttlout_list[i].on()
        #                 elif ttlCommandArr[i] == -1:
        #                     self.ttlout_list[i].off()
        #     #program DDS sequence
        #     for timestamp, params in dds_single_sequence:
        #
        #     #program DDS Ramp
        #     #program PMT input
        #     for i in range(0, tmax_us, self.pmt_interval):
        #         time_pmt = PMT_device.gate_rising_mu(self.pmtInterval * us)
        #         counts_pmt = PMT_device.count(time_pmt)
        #         self.mutate_dataset(self.PMT_count, i, counts_pmt)
        #     #todo: program dds
        #     #todo: program ttls for dds's

    def runsCompleted(self):
        val1 = self.get_dataset('numRuns')
        return val1[0]

    def disconnect(self):
        self.core.close()
        self.scheduler.pause()

    @kernel
    def eraseSequence(self, sequencename):
        self.core.reset()
        self.core_dma.erase(sequencename)

    def setTTL(self, ttlname, state):
        self.core.reset()
        self.ttl_dev = self.ttlout_list[ttlname]
        self._setTTL(state)

    @kernel
    def _setTTL(self, state):
        self.core.reset()
        if state:
            self.ttl_dev.on()
        else:
            self.ttl_dev.off()

    @kernel
    def initializeDDS(self):
        '''
        Force reprogram of all dds chips during initialization
        '''
        #reset dds
        self.core.reset()
        for device in self.dds_list.values():
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        self.core.reset()

        #reset urukul cpld
        for device in self.urukul_list.values():
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        self.core.reset()

    def setPMTMode(self, mode):
        self.pmt_mode = mode

    def setPMTInterval(self, time_us):
        self.pmt_interval_us = time_us