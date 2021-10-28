"""
Used by the pulser server to store a pulse sequence
"""

import numpy, array
from decimal import Decimal

#todo: use seconds to mu instead of sectostep

from EGGS_labrad.lib.config.hardwareConfiguration import hardwareConfiguration

class Sequence():
    """Sequence for programming pulses"""
    def __init__(self, parent):
        self.channelTotal = hardwareConfiguration.channelTotal
        self.timeResolution = Decimal(hardwareConfiguration.timeResolution)
        self.MAX_SWITCHES = hardwareConfiguration.maxSwitches

        #dictionary in the form time:which channels to switch
        #time is expressed as timestep with the given resolution
        #which channels to switch is a channelTotal-long array with 1 to switch ON, -1 to switch OFF, 0 to do nothing
        self.switchingTimes = {0:numpy.zeros(self.channelTotal, dtype = numpy.int8)}
        self.switches = 1 #keeps track of how many switches are to be performed (same as the number of keys in the switching Times dictionary)

        #dictionary for storing information about dds switches, in the format:
        #timestep: {channel_name: integer representing the state}
        self.ddsSettingList = dict.fromkeys(self.parent.ddsDict.keys(), [])
        self.sectomu = self.parent.sectomu

    #TTL functions
    def addPulse(self, channel, start, duration):
        """adding TTL pulse, times are in seconds"""
        start = self.secToStep(start)
        duration = self.secToStep(duration)
        self._addNewSwitch(start, channel, 1)
        self._addNewSwitch(start + duration, channel, -1)

    def extendSequenceLength(self, timeLength):
        """Allows to extend the total length of the sequence"""
        timeLength = self.secToStep(timeLength)
        self._addNewSwitch(timeLength,0,0)

    def _addNewSwitch(self, timeStep, chan, value):
        if timeStep in self.switchingTimes:
            if self.switchingTimes[timeStep][chan]: # checks if 0 or 1/-1
                # if set to turn off, but want on, replace with zero, fixes error adding 2 TTLs back to back
                if self.switchingTimes[timeStep][chan] * value == -1:
                    self.switchingTimes[timeStep][chan] = 0
                else:
                    raise Exception ('Double switch at time {} for channel {}'.format(timeStep, chan))
            else:
                self.switchingTimes[timeStep][chan] = value
        else:
            if self.switches == self.MAX_SWITCHES: raise Exception("Exceeded maximum number of switches {}".format(self.switches))
            self.switchingTimes[timeStep] = numpy.zeros(self.channelTotal, dtype = numpy.int8)
            self.switches += 1
            self.switchingTimes[timeStep][chan] = value

    #DDS functions
    def addDDS(self, name, start_time, params, start_or_stop):
        start_time_mu = self.sectomu(start_time)
        self.ddsSettingList[name].append((start_time, params, start_or_stop))

    def parseDDS(self):
        #sort settings by start time
        for channel_name in self.ddsSettingList.keys():
            self.ddsSettingList[channel_name] = sorted(dds_setting, key=lambda t: t[0])
        # for channel_name, dds_settings in self.ddsSettingList.keys():
        # # check for possible errors
        #     # check if pulse endpoints meet
        # if start_time == end_time:
        #     # program if new pulse
        #     if (end_typ == 'stop') and (new_typ == 'start'):
        #         possibleError = (0, '')
        #     # don't program if zero-length pulse
        #     elif end_typ == 'start' and new_typ == 'stop':
        #         possibleError = (0, '')
        #         continue
        # # check if pulses overlap
        # elif end_typ == new_typ:
        #     possibleError = (start_time, 'Found Overlap Of Two Pulses for channel {}'.format(name))


    #Human representation
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
