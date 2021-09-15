from artiq.experiment import *

import labrad
import numpy as np
import array


class api(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("scheduler")

        self.ttl_list = [self.get_device()]

    def _parseSequence(self, sequence):
        '''
        Converts the ttl sequence from parseTTL() into a more ARTIQ-friendly format

        Args:
            sequence (bytearray): the ttl pulse sequence from parseTTL()

        Returns:

        '''
        sequence = np.array(sequence)
        sequence = sequence.reshape(len(sequence), 4)

        pulse_times = np.sum(sequence[::2], 1)
        ttl_sequence = sequence[1::2]

        delay_lengths = pulse_times[1:] - pulse_times[:-1]
        ttl_change = ttl_sequence[1:] - ttl_sequence[:-1]

        ttl_commands =

        return

    @kernel
    def programBoard(self, sequence):
        parsed_sequence = _parseSequence(sequence)
        with self.core_dma.record("pulse_sequence"):
            for delay_val_us, ttlCommands in parsed_sequence:
                with parallel:
                    for command in ttlCommands:
                        self.command
                delay(delay_val_us * us)

    def startLooped(self):
        '''
        Start the pulse sequence and make it loop forever
        '''

    def stopLooped(self):
        '''
        Stop the pulse sequence (but will loop forever again if started
        '''

    def startSingle(self):
        '''
        Start a single iteration of the pulse sequence
        '''

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
        check if the pulse sequece is done executing or not
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