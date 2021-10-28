"""
Used by the pulser server to store a pulse sequence
"""

import numpy, array
from decimal import Decimal

#from EGGS_labrad.lib.config.hardwareConfiguration import hardwareConfiguration

class Sequence():
    """Sequence for programming pulses"""

    # def __init__(self, parent):
    #     self.channelTotal = hardwareConfiguration.channelTotal
    #     self.MAX_SWITCHES = hardwareConfiguration.maxSwitches
    #
    #     #dictionary in the form time:which channels to switch
    #     #which channels to switch is a channelTotal-long array with 1 to switch ON, -1 to switch OFF, 0 to do nothing
    #     self.switchingTimes = {0:numpy.zeros(self.channelTotal, dtype = numpy.int8)}
    #     self.switches = 1 #keeps track of how many switches are to be performed (same as the number of keys in the switching Times dictionary)
    #
    #     #dictionary for storing information about dds switches, in the format:
    #     #time: {channel_name: integer representing the state}
    #     self.ddsSettingList = dict.fromkeys(self.parent.ddsDict.keys(), [])
    #     self.sectomu = self.parent.sectomu

    def __init__(self):
        self.channelTotal = 8
        self.timeResolution = 1
        self.MAX_SWITCHES = 1000

        self.switchingTimes = {0:numpy.zeros(self.channelTotal, dtype = numpy.int8)}
        self.switches = 1

        self.ddsSettingList = {}
        self.sectomu = lambda a: a


    #Sequence functions
    def progRepresentation(self):
        """Returns the programming representation of the sequence"""
        return self.ddsSettings, self.ttlProgram

    def humanRepresentation(self):
        """Returns the human readable version of the sequence for FPGA for debugging"""
        ttl = self.ttlHumanRepresentation(self.ttlProgram)
        dds = self.ddsHumanRepresentation(self.ddsSettings)
        return ttl, dds

    def ddsHumanRepresentation(self, dds):
        program = []
        print(dds)
        for name, buf in dds.items():
            print("name is ", name)
            arr = array.array('B', buf)
            # remove termination
            arr = arr[:-2]
            channel = hardwareConfiguration.ddsDict[name]
            coherent = channel.phase_coherent_model
            freq_min, freq_max = channel.boardfreqrange
            ampl_min, ampl_max = channel.boardamplrange
            #get conversion from binary to values, 65535 = 16 bit max
            freq_conv = (freq_max - freq_min) / float(65535)
            ampl_conv = (ampl_max - ampl_min) / float(65535)
            def chunks(l, n):
                """ Yield successive n-sized chunks from l."""
                for i in range(0, len(l), n):
                    yield l[i:i+n]
            if coherent:
                for a0, a1, amp0, amp1, a2, a3, a4, a5, f0, f1, f2, f3, f4, f5, f6, f7, in chunks(arr, 16):
                    freq_num = (f7 << 24) + (f6 << 16) + (f5 << 8) + f4
                    ampl_num = (amp1 << 8) + amp0
                    freq = freq_min + freq_num * freq_conv
                    print("freq: ", freq)
                    ampl = ampl_min + ampl_num * ampl_conv
                    print("ampl: ", ampl)
                    program.append((name, freq, ampl))
            else:
                for a, b, c, d in chunks(arr, 4):
                    freq_num = (b << 8) + a
                    ampl_num = (d << 8) + c
                    freq = freq_min + freq_num * freq_conv
                    ampl = ampl_min + ampl_num * ampl_conv
                    program.append((name, freq, ampl))
        return program

    def ttlHumanRepresentation(self, rep):
        # recast rep from bytearray into string
        rep = str(rep)
        # does the decoding from the string
        arr = numpy.fromstring(rep, dtype = numpy.uint16)
        #arr = numpy.frombuffer(rep, dtype = numpy.uint16)
        # once decoded, need to be able to manipulate large numbers
        arr = numpy.array(arr, dtype = numpy.uint32)
        #arr = numpy.array(rep,dtype = numpy.uint16)
        arr = arr.reshape(-1,4)
        times = ((arr[:,0] << 16) + arr[:,1]) * float(self.timeResolution)
        channels = ((arr[:,2] << 16) + arr[:,3])

        def expandChannel(ch):
            '''function for getting the binary representation, i.e 2**32 is 1000...0'''
            expand = bin(ch)[2:].zfill(32)
            reverse = expand[::-1]
            return reverse

        channels = map(expandChannel, channels)
        return numpy.vstack((times, channels)).transpose()

    #TTL functions
    def addPulse(self, channel, start, duration):
        """
        Adds TTL pulse to sequence
        Arguments:
            channel     (int)   : the TTL channel number
            start       (float) : the start time in seconds
            duration    (float) : the pulse duration in seconds
        """
        start = self.sectomu(start)
        duration = self.sectomu(duration)
        self._addNewSwitch(start, channel, 1)
        self._addNewSwitch(start + duration, channel, -1)

    def extendSequenceLength(self, endtime):
        """
        Extend the total length of the TTL sequence
        Arguments:
            endtime (int): the TTL sequence endtime in seconds
        """
        endtime_mu = self.sectomu(endtime)
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
            self.switchingTimes[start_time] = numpy.zeros(self.channelTotal, dtype = numpy.int8)
            self.switches += 1
            self.switchingTimes[start_time][chan] = value

    #DDS functions
    def addDDS(self, dds_num, start_time, params, start_or_stop):
        start_time_mu = self.sectomu(start_time)
        self.ddsSettingList[start_time_mu] = (dds_num, start_time, params, start_or_stop)
