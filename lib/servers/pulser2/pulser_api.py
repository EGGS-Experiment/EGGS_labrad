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
    Pulser API: an ARTIQ EnvExperiment class that hosts all necessary device functions.
    Its main sequence runs a LabRAD server.
    Needs to be submitted to the ARTIQ master to run properly.
    """

    def build(self):
        #setup
        self._getDevices()
        self._setVariables()
        self._getConfig()

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
            #create holding lists (dict not supported in kernel methods)
        self.ttlout_list = list()
        self.ttlin_list = list()
        self.dds_list = list()
        self.urukul_list = list()
        self.pmt_list = list()
        self.linetrigger_list = list()
        self.th1 = {0:[1,1]}

        #assign names and devices
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            #set device as attribute
            devicetype = params['class']
            device = self.get_device(name)
            self.setattr_device(name)
            if devicetype == 'TTLInOut':
                self.ttlin_list.append(device)
            elif devicetype == 'TTLOut':
                if 'pmt' in name:
                    self.pmt_list.append(device)
                elif 'linetrigger' in name:
                    self.linetrigger_list.append(device)
                elif 'urukul' not in name:
                    self.ttlout_list.append(device)
            elif devicetype == 'AD9910':
                self.dds_list.append(device)
            elif devicetype == 'CPLD':
                self.urukul_list.append(device)

    def _setVariables(self):
        """
        Set up internal variables.
        """
        #sequencer variables
        #pmt variables
        self.pmt_interval = 0
        self.pmt_mode = 0 #0 is normal/automatic, 1 is differential
        self.pmt_arraylength = 10000
        self.set_dataset('pmt_counts', np.full(self.pmt_arraylength, np.nan))

    def _getConfig(self):
        """
        Set up relevant device configs from config file.
        """
        pass

    def _initializeDevices(self):
        """
        Initialize devices that need to be initialized.
        """
        #initialize devices
            #set ttlinout devices to be input
        self.core.reset()
        for device in self.ttlin_list:
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

    @kernel
    def _record(self, sequencename):
        self.core.reset()
        with self.core_dma.record(sequencename):
            for i in range(50):
                with parallel:
                    self.ttlout_list[0].pulse(1*ms)
                    self.ttlout_list[1].pulse(1*ms)
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

    def record(self, sequencename):
        """
        Processes the TTL and DDS sequence into a format
        more easily readable and processable by ARTIQ.
        """
        #todo: config
        self._record(sequencename)

    def runsCompleted(self):
        """
        Return the number of pulse sequence runs completed.
        """
        runs = self.get_dataset('numRuns')
        return runs[0]

    def disconnect(self):
        """
        Disconnect the API from the master.
        """
        self.core.close()
        self.scheduler.pause()

    @kernel
    def eraseSequence(self, sequencename):
        """
        Erase the given pulse sequence from DMA.
        """
        self.core.reset()
        self.core_dma.erase(sequencename)

    @kernel
    def setTTL(self, ttlnum, state):
        """
        Manually set the state of a TTL.
        """
        self.core.reset()
        if state:
            self.ttlout_list[ttlnum].on()
        else:
            self.ttlout_list[ttlnum].off()

    #DDS functions
    @kernel
    def initializeDDS(self):
        '''
        Force reprogram of all dds chips during initialization.
        '''
        #todo: test
        self.core.reset()
        for device in self.dds_list:
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        self.core.reset()

        #reset urukul cpld
        for device in self.urukul_list:
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        self.core.reset()

    @kernel
    def toggleDDS(self, ddsnum, state):
        self.dds_list[ddsnum].cfg_sw(state)

    @kernel
    def setDDS(self, ddsnum, params, _profile):
        """
         Manually set the state of a DDS.
         """
        _ftw = params[0]
        _asf = params[1]
        _pow = params[2]
        self.dds_list[ddsnum].set_mu(ftw = _freq, asf = _ampl, pow = _pow, profile = _profile)
        #todo: do we need to change profile to desired one?
        #todo: test

    #PMT functions
    def setPMTMode(self, mode):
        self.pmt_mode = mode

    def setPMTInterval(self, time_us):
        self.pmt_interval_us = time_us