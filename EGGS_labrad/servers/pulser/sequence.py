import numpy as np
import array

#from EGGS_labrad.config.hardwareConfiguration import hardwareConfiguration

class Sequence():
    """
    Sequence for programming pulses.
    Used by the Pulser server to store a pulse sequence.
    """

    # def __init__(self, parent):
    #     self.channelTotal = hardwareConfiguration.channelTotal
    #     self.MAX_SWITCHES = hardwareConfiguration.maxSwitches
    #
    #     #dictionary in the form: {time: which channels to switch}
    #     #which channels to switch is a channelTotal-long array with 1 to switch ON, -1 to switch OFF, 0 to do nothing
    #     self.switchingTimes = {0: np.zeros(self.channelTotal, dtype = np.int8)}
    #     self.switches = 1 #keeps track of how many switches are to be performed (same as the number of keys in the switching Times dictionary)
    #
    #     #dictionary for storing information about dds switches, in the format:
    #     #time: {channel_name: integer representing the state}
    #     self.ddsSettingList = dict.fromkeys(hardwareConfiguration.ddsDict.keys(), [])
    #     self.seconds_to_mu = self.parent.seconds_to_mu

    def __init__(self):
        self.channelTotal = 8
        self.timeResolution = 1
        self.MAX_SWITCHES = 1000

        self.switchingTimes = {0: np.zeros(self.channelTotal, dtype = np.int8)}
        self.switches = 1

        self.ddsSettingList = {}

    #Sequence functions
    def progRepresentation(self):
        """Returns the programming representation of the sequence"""
        return self.switchingTimes, self.ddsSettingList

    def humanRepresentation(self):
        """Returns the human readable version of the sequence for FPGA for debugging"""
        ttl = self.ttlHumanRepresentation(self.ttlProgram)
        return ttl, self.ddsSettingList

    def ttlHumanRepresentation(self, rep):
        # recast rep from bytearray into string
        rep = str(rep)
        # does the decoding from the string
        arr = np.fromstring(rep, dtype = np.uint16)
        # once decoded, need to be able to manipulate large numbers
        arr = np.array(arr, dtype = np.uint32)
        arr = arr.reshape(-1,4)
        times = ((arr[:, 0] << 16) + arr[:, 1]) * float(self.timeResolution)
        channels = ((arr[:, 2] << 16) + arr[:, 3])

        def expandChannel(ch):
            '''function for getting the binary representation, i.e 2**32 is 1000...0'''
            expand = bin(ch)[2:].zfill(32)
            reverse = expand[::-1]
            return reverse

        channels = map(expandChannel, channels)
        return np.vstack((times, channels)).transpose()

    #TTL functions
    def addPulse(self, channel, start, duration):
        """
        Adds TTL pulse to sequence
        Arguments:
            channel     (int)   : the TTL channel number
            start       (float) : the start time in seconds
            duration    (float) : the pulse duration in seconds
        """
        start = self.seconds_to_mu(start)
        duration = self.seconds_to_mu(duration)
        self._addNewSwitch(start, channel, 1)
        self._addNewSwitch(start + duration, channel, -1)

    def extendSequenceLength(self, endtime):
        """
        Extend the total length of the TTL sequence
        Arguments:
            endtime (int): the TTL sequence endtime in seconds
        """
        endtime_mu = self.seconds_to_mu(endtime)
        self._addNewSwitch(endtime_mu, 0, 0)

    def _addNewSwitch(self, start_time, chan, value):
        if start_time in self.switchingTimes:
            if self.switchingTimes[start_time][chan]: # checks if 0 or 1/-1
                # if set to turn off, but want on, replace with zero, fixes error adding 2 TTLs back to back
                if self.switchingTimes[start_time][chan] * value == -1:
                    self.switchingTimes[start_time][chan] = 0
                else:
                    raise Exception ('Double switch at time {} for channel {}'.format(start_time, chan))
            else:
                self.switchingTimes[start_time][chan] = value
        else:
            if self.switches == self.MAX_SWITCHES: raise Exception("Exceeded maximum number of switches {}".format(self.switches))
            self.switchingTimes[start_time] = np.zeros(self.channelTotal, dtype = np.int8)
            self.switches += 1
            self.switchingTimes[start_time][chan] = value

    #DDS functions
    def addDDS(self, dds_num, start_time, params, start_or_stop):
        start_time_mu = self.seconds_to_mu(start_time)
        self.ddsSettingList[start_time_mu] = (dds_num, params, start_or_stop)
