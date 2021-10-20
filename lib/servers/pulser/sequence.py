import numpy, array

from decimal import Decimal

class Sequence():
    """Sequence for programming pulses"""
    def __init__(self, parent):
        self.parent = parent
        self.channelTotal = hardwareConfiguration.channelTotal
        self.timeResolution = Decimal(hardwareConfiguration.timeResolution)
        self.MAX_SWITCHES = hardwareConfiguration.maxSwitches
        self.resetstepDuration = hardwareConfiguration.resetstepDuration
        #dictionary in the form time:which channels to switch
        #time is expressed as timestep with the given resolution
        #which channels to switch is a channelTotal-long array with 1 to switch ON, -1 to switch OFF, 0 to do nothing
        self.switchingTimes = {0:numpy.zeros(self.channelTotal, dtype = numpy.int8)}
        self.switches = 1 #keeps track of how many switches are to be performed (same as the number of keys in the switching Times dictionary"
        #dictionary for storing information about dds switches, in the format:
        #timestep: {channel_name: integer representing the state}
        self.ddsSettingList = []
        self.advanceDDS = hardwareConfiguration.channelDict['AdvanceDDS'].channelnumber
        self.resetDDS = hardwareConfiguration.channelDict['ResetDDS'].channelnumber

    def addDDS(self, name, start, num, typ):
        timeStep = self.secToStep(start)
        self.ddsSettingList.append((name, timeStep, num, typ))

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

    def secToStep(self, sec):
        '''converts seconds to time steps'''
        start = '{0:.9f}'.format(sec) #round to nanoseconds
        start = Decimal(start) #convert to decimal
        step = ( start / self.timeResolution).to_integral_value()
        step = int(step)
        return step

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

    def progRepresentation(self, parse = True):
        if parse:
            self.ddsSettings = self.parseDDS()
            self.ttlProgram = self.parseTTL()
        return self.ddsSettings, self.ttlProgram

    def userAddedDDS(self):
        return bool(len(self.ddsSettingList))

    def parseDDS(self):
        if not self.userAddedDDS():
            return None
        state = self.parent._getCurrentDDS()
        #keeps track of end time and
        pulses_end = {}.fromkeys(state, (0, 'stop'))
        dds_program = {}.fromkeys(state, '')
        lastTime = 0
        #get each DDS pulse as (name, time, RAM, on/off)
        entries = sorted(self.ddsSettingList, key = lambda t: t[1] ) #sort by starting time
        possibleError = (0, '')
        while True:
            try:
                name, start, num, typ = entries.pop(0)
            except IndexError:
                if start  == lastTime:
                    #still have unprogrammed entries
                    self.addToProgram(dds_program, state)
                    self._addNewSwitch(lastTime, self.advanceDDS, 1)
                    self._addNewSwitch(lastTime + self.resetstepDuration, self.advanceDDS, -1)
                #add termination
                for name in iter(dds_program):
                    dds_program[name] += '\x00\x00'
                #at the end of the sequence, reset dds
                lastTTL = max(self.switchingTimes.keys())
                self._addNewSwitch(lastTTL, self.resetDDS, 1)
                self._addNewSwitch(lastTTL + self.resetstepDuration, self.resetDDS, -1)
                return dds_program
            end_time, end_typ = pulses_end[name]
            # the time has advanced, so need to program the previous state
            if start > lastTime:
                #raise exception if error exists and belongs to that time
                if possibleError[0] == lastTime and len(possibleError[1]):
                    raise Exception(possibleError[1])
                self.addToProgram(dds_program, state)
                #move RAM to next position
                if not lastTime == 0:
                    self._addNewSwitch(lastTime,self.advanceDDS,1)
                    self._addNewSwitch(lastTime + self.resetstepDuration, self.advanceDDS, -1)
                lastTime = start
            #move to next dds pulse
            if start == end_time:
                if end_typ == 'stop' and typ == 'start':
                    possibleError = (0, '')
                    state[name] = num
                    pulses_end[name] = (start, typ)
                elif end_typ == 'start' and typ == 'stop':
                    possibleError = (0, '')
            elif end_typ == typ:
                possibleError = (start, 'Found Overlap Of Two Pulses for channel {}'.format(name))
                state[name] = num
                pulses_end[name] = (start, typ)
            else:
                state[name] = num
                pulses_end[name] = (start, typ)

    def addToProgram(self, prog, state):
        for name, num in state.items():
            if not hardwareConfiguration.ddsDict[name].phase_coherent_model:
                buf = self.parent._intToBuf(num)
            else:
                buf = self.parent._intToBuf_coherent(num)
            prog[name] += buf

    def parseTTL(self):
        """Returns the representation of the sequence for programming the FPGA"""
        rep = ''
        lastChannels = numpy.zeros(self.channelTotal)
        powerArray = 2**numpy.arange(self.channelTotal, dtype = numpy.uint64)
        for key, newChannels in sorted(self.switchingTimes.items()):
            # computes the action of switching on the state
            channels = lastChannels + newChannels
            if (channels < 0).any():
                raise Exception('Trying to switch off channel that is not already on')
            channelInt = numpy.dot(channels, powerArray)
            # converts the new state to hex and adds it to the sequence
            rep = rep + hex(key) + hex(channelInt)
            lastChannels = channels
        # adding termination
        rep = rep + 2*hex(0)
        return rep

    def humanRepresentation(self):
        """Returns the human readable version of the sequence for FPGA for debugging"""
        dds, ttl = self.progRepresentation(parse = False)
        ttl = self.ttlHumanRepresentation(ttl)
        dds = self.ddsHumanRepresentation(dds)
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
