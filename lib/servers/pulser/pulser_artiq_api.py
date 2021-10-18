from labrad import util

from artiq.experiment import *
from pulser_artiq import Pulser_artiq
from devices import Devices

import numpy as np
#todo: convert all time units to seconds
class api(EnvExperiment):
    kernel_invariants = {}

    #Experiment stages
    def build(self):
        self._getDevices()
        self._setVariables()

    @kernel
    def prepare(self):
        self._initializeDevices()

    def run(self):
        #run the labrad server and expose class methods to the server
        util.runServer(Pulser_artiq(self))

    #Setup functions
    def _getDevices(self):
        #get core
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("scheduler")

        #get device names
        self.device_db = self.get_device_db()
            #get ttl names
        ttl_names = [key for key, val in self.device_db if val['class'] == 'TTLOut']
            #get ttl names
        ttlin_names = [key for key, val in self.device_db if val['class'] == 'TTLInOut']
            #get dds names
        dds_names = [key for key, val in self.device_db if val['class'] == 'AD9910' or 'AD9912']
            #get urukul names
        urukul_names = [key for key, val in self.device_db if val['class'] == 'CPLD']

        #todo: do DAC and ADC

        #set device attributes
        for name in ttl_names + ttlin_names + dds_names + urukul_names:
            self.setattr_device(name)

        #get devices
        self.ttl_list = {name: self.get_device(name) for name in ttl_names}
        self.ttlin_list = {name: self.get_device(name) for name in ttlin_names}
        self.dds_list = {name: self.get_device(name) for name in dds_names}
        self.urukul_list = {name: self.get_device(name) for name in urukul_names}

    def _setVariables(self):
        #sequencer variables
        self.numRuns = 0
        self.maxRuns = 0
        #pmt variables
        self.pmtInterval = 0
        self.pmtMode = 0 #0 is normal/automatic, 1 is differential
        #todo: add correct number of samples
        self.setattr_dataset('PMT_count', np.full(num_samples, np.na))
        #linetrigger variables
        self.linetrigger_delay = 0 * us
        self.linetrigger_active = False
        #todo: PMT FIFO

    @kernel
    def _initializeDevices(self):
        #initialize devices
            #set ttlinout devices to be input
        for device in self.ttlin_list.values():
            device.input()
            #initialize DDSs
        for device in self.dds_list.values():
            device.init()
        for device in self.urukul_list.values():
            device.init()
        #todo: set attenuator, etc

    #Sequence functions
    @kernel(flags = {"fast-math"})
    def programSequence(self, ttl_sequence, dds_single_sequence, dds_ramp_sequence):
        #record pulse sequence in memory
        PMT_device = self.ttlin_list['PMT']
        #todo: calculate number of PMT recordings needd
        with self.core_dma.record("pulse_sequence"):
            #add ttl sequence
            for timestamp, ttlCommandArr in ttl_sequence:
                at_mu(timestamp)
                with parallel:
                    #todo: convert to name format
                    for i in range(ttl_sequence.channelTotal):
                        if ttlCommandArr[i] == 1:
                            self.ttl_list[i].on()
                        elif ttlCommandArr[i] == -1:
                            self.ttl_list[i].off()
            #todo: program DDS
            for i in range():
                time_pmt = PMT_device.gate_rising(self.pmtInterval)
                counts_pmt = PMT_device.count(time_pmt)
                self.mutate_dataset(self.PMT_count, i, counts_pmt)


    @kernel
    def runSequence(self, runs):
        self.core.reset()
        self.maxRuns = runs

        #get sequence handle to minimize overhead
        sequence_handle = self.core_dma.get_handle("pulse_sequence")

        #wait until line trigger receives input or we disable the line trigger
        while self.linetrigger_active:
            #wait in blocks of 10ms
            time_gate = self.ttlin_list['LineTrigger'].gate_rising(10 * ms)
            time_trig = self.ttlin_list['LineTrigger'].timestamp_mu(time_gate)
            #time_trig returns -1 if we dont receive a signal
            if time_trig > 0:
                #set time to now and do an offset delay
                delay(self.linetrigger_delay)
                break

        #reset time and start running
        while self.numRuns < self.maxRuns:
            self.core.reset()
            self.core_dma.playback_handle(sequence_handle)
            self.numRuns += 1
            #todo: is this possible? can we change variables?

        #todo: process data
        #todo: transfer data

    @kernel
    def stopSequence(self):
        '''
        Stops any currently running sequence
        '''
        self.maxRuns = 0

    @kernel
    def eraseSequence(self):
        '''
        Removes the pulse sequence from memory
        '''
        self.core_dma.erase("pulse_sequence")

    @kernel
    def numRepetitions(self):
        '''
        check if the pulse sequence is done executing or not
        '''
        return self.numRuns
        #todo: kernel typing???

    #TTL functions
    def setAuto(self, channel, inversion):
        '''
        Set the logic of the TTL to be auto or not
        '''


    def setManual(self, channel, state):
        '''
        Set the logic of the TTL to be manual or not
        '''


    #PMT functions
    def setMode(self, mode):
        """
        User selects PMT counting rate
        """
        if mode == 0:
            self.pmtMode = 0
        elif mode == 1:
            self.pmtMode = 1

    def setPMTCountInterval(self, time):
        '''
        Set count rate of PMT in ms
        '''
        self.pmtInterval = time * us

    def getReadoutCounts(self, number):
        '''
        Get the readout count data.
        '''
        #remove np.nan
        return self.

    def resetReadoutCounts(self):
        '''
        Reset the FIFO on the FPGA for the read-out count.
        '''
        #todo: calculate num samples
        self.set_dataset('PMT_count', np.full(num_samples, np.nan))

    #DDS functions
    @kernel
    def resetAllDDS(self):
        '''
        Reset the ram position of all dds chips to 0
        '''
        #not easily possible since FPGA RAM isn't exposed as part of artiq API
        pass

    @kernel
    def advanceAllDDS(self):
        '''
        Advance the ram position of all dds chips
        '''
        # not easily possible since FPGA RAM isn't exposed as part of artiq API
        pass

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

    @kernel
    def setDDSParam(self, chan, _asf, _ftw, **kwargs):
        self.dds_list[chan].set_mu(ftw = _ftw, asf = _asf)
        if kwargs is not None:
            self.dds_list[chan].set_mu(kwargs)

    #LineTrigger functions
    def enableLineTrigger(self, delay = 0):
        '''
        Enable line trigger with some delay (in microseconds)
        '''
        self.linetrigger_active = True
        self.linetrigger_delay = delay * us

    def disableLineTrigger(self):
        '''
        Disable the line trigger
        '''
        self.linetrigger_active = False

