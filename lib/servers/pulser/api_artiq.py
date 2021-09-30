from artiq.experiment import *

import labrad, array
import numpy as np


class api(EnvExperiment):
    kernel_invariants = {}

    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("scheduler")

        #get devices
        self.ttl_list = [self.get_device()]

        #initialize devices?

        #setup variables
        #find timestep
        self.ms_to_mu = us/self.core.ref_period

    @kernel(flags = {"fast-math"})
    def programBoard(self, sequence):
        with self.core_dma.record("pulse_sequence"):
            for timestamp, ttlCommandArr in sequence:
                self.core.set_time_mu(int(timestamp * self.ms_to_mu))
                with parallel:
                    for i in range(sequence.channelTotal):
                        if ttlCommandArr[i] = 1:
                            self.ttl_list[i].on()
                        elif ttlCommandArr[i] = -1:
                            self.ttl_list[i].off()


    def startLooped(self):
        '''
        Start the pulse sequence and make it loop forever
        '''


    def stopLooped(self):
        '''
        Stop the pulse sequence (but will loop forever again if started)
        '''

    def startSingle(self):
        '''
        Start a single iteration of the pulse sequence
        '''
        self.core_dma.playback("pulse_sequence")

    def stopSingle(self):
        '''
        Stop the single iteration of the pulse sequence
        '''

    def setNumberRepeatitions(self, number):
        '''
        For a finite number of iteration, set the number of iteration
        '''

    def resetRam(self):
        '''
        Reset the ram position of the pulser. Important to do this before writing the new sequence.
        '''
        self.core_dma.erase("pulse_sequence")

    def resetSeqCounter(self):
        '''
        Reset the counter to see how many iterations have been executed.
        '''

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

    def isSeqDone(self):
        '''
        check if the pulse sequence is done executing or not
        '''

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

    def howManySequencesDone(self):
        '''
        Get the number of iteratione executed.
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

    def padTo16(self,data):
        '''
        Padding function to make the data a multiple of 16
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

    def enableLineTrigger(self, delay = 0):
        '''
        sets delay value in microseconds
        '''

    def disableLineTrigger(self):
        '''

        '''