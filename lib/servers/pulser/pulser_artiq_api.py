from labrad import util

from artiq.experiment import *
from pulser_artiq_server import Pulser_artiq
from devices import Devices

import numpy as np

class api(EnvExperiment):
    kernel_invariants = {}

    def build(self):
        #get core
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("scheduler")

        #get device names
        self.device_db = self.get_device_db()
            #get ttl names
        ttl_names = [key for key, val in self.device_db if val['class'] == 'TTLOut' or 'TTLInOut']
            #get dds names
        dds_names = [key for key, val in self.device_db if val['class'] == 'AD9910' or 'AD9912']
            #get urukul names
        urukul_names = [key for key, val in self.device_db if val['class'] == 'CPLD']

        #todo: do DAC and ADC
        #todo: do PMT via TTL

        #set device attributes
        for name in ttl_names + dds_names + urukul_names:
            self.setattr_device(name)

        #get devices
        self.ttl_list = [self.get_device(name) for name in ttl_names]
        self.dds_list = [self.get_device(name) for name in dds_names]
        self.urukul_list = [self.get_device(name) for name in urukul_names]

        #initialize devices
        for device in self.dds_list + urukul_list:
            device.init()

        #setup variables
        self.numRuns = 0
        self.maxRuns = 0

    #Pulse sequencer functions
    @kernel(flags = {"fast-math"})
    def programSequence(self, sequence):
        #TODO: program dds
        with self.core_dma.record("pulse_sequence"):
            for timestamp, ttlCommandArr in sequence:
                #convert time to machine units and set cursor to correct time
                self.core.set_time_mu(timestamp)
                with parallel:
                    for i in range(sequence.channelTotal):
                        if ttlCommandArr[i] == 1:
                            self.ttl_list[i].on()
                        elif ttlCommandArr[i] == -1:
                            self.ttl_list[i].off()

        #get sequence handle to minimize overhead when we have to run sequence
        self.sequence_handle = self.core_dma.get_handle("pulse_sequence")

    @kernel
    def runSequence(self):
        while self.numRuns < self.maxRuns:
            self.core.reset()
            self.core_dma.playback_handle(self.sequence_handle)
            self.numRuns += 1

    @kernel
    def resetRam(self):
        '''
        Reset the ram position of the pulser. Important to do this before writing the new sequence.
        '''
        self.core_dma.erase("pulse_sequence")

    def resetFIFONormal(self):
        '''
        Reset the FIFO on the FPGA for the normal PMT counting
        '''

    def resetFIFOResolved(self):
        '''
        Reset the FIFO on the FPGA for the time-tagged photon counting
        '''

    def resetFIFOReadout(self):
        '''
        Reset the FIFO on the FPGA for the read-out count.
        '''

    def setModeNormal(self):
        """
        user selects PMT counting rate
        """

    def setModeDifferential(self):
        """
        pulse sequence controls the PMT counting rate
        """

    @kernel(flags={"fast-math"})
    def isSeqDone(self):
        '''
        check if the pulse sequence is done executing or not
        '''
        return self.numRuns

    def getResolvedTotal(self):
        '''
        Get the number of photons counted in the FIFO for the time-resolved photon counter.
        '''

    def getResolvedCounts(self, number):
        '''
        Get the time-tagged photon data.
        '''

    def getNormalTotal(self):
        '''
        Get the number of normal PMT counts. (How many data in the FIFO)
        '''

    def getNormalCounts(self, number):
        '''
        Get the normal PMT counts from the FIFO.
        '''

    def getReadoutTotal(self):
        '''
        Get the number of readout count.
        '''

    def getReadoutCounts(self, number):
        '''
        Get the readout count data.
        '''

    def setPMTCountRate(self, time):
        '''

        '''

    def setAuto(self, channel, inversion):
        '''
        Set the logic of the TTL to be auto or not
        '''

    def setManual(self, channel, state):
        '''
        Set the logic of the TTL to be manual or not
        '''

    def resetAllDDS(self):
        '''
        Reset the ram position of all dds chips to 0
        '''

    def advanceAllDDS(self):
        '''
        Advance the ram position of all dds chips
        '''

    def setDDSchannel(self, chan):
        '''
        select the dds chip for communication
        '''

    @kernel
    def programDDS(self, prog):
        '''
        program the dds channel with a list of frequencies and amplitudes. The channel of the particular channel must be selected first
        '''

    def initializeDDS(self):
        '''
        force reprogram of all dds chips during initialization
        '''
        for device in self.dds_list + urukul_list:
            device.init()
        #todo: check if this actually works

    def enableLineTrigger(self, delay = 0):
        '''
        sets delay value in microseconds
        '''

    def disableLineTrigger(self):
        '''

        '''

    def run(self):
        util.runServer(Pulser_artiq(self))