from labrad import util

from artiq.experiment import *
from pulser_artiq import Pulser_artiq

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
            #create holding dictionaries
        self.ttlout_list = dict()
        self.ttlin_list = dict()
        self.dds_list = dict()
        self.urukul_list = dict()
        self.pmt_list = dict()
        self.linetrigger_list = dict()

        #assign names and devices
        for name, params in self.device_db:
            self.setattr(name)
            if params['class'] == 'TTLInOut':
                self.ttlin_list[name] = self.get_device(name)
            elif (params['class'] == 'TTLOut'):
                if 'pmt' in name:
                    self.pmt_list[name] = self.get_device(name)
                elif 'linetrigger' in name:
                    self.linetrigger_list[name] = self.get_device(name)
                elif 'urukul' not in name:
                    self.ttlout_list[name] = self.get_device(name)
            elif params['class'] == 'AD9910':
                #get DDS component names and devices
                args = params['arguments']
                    #CPLD (i.e. urukul)
                cpld_name = args['cpld_device']
                cpld_dev = self.get_device(cpld_name)
                    #DDS on/off switch
                sw_name = args['sw_device']
                sw_dev = self.get_device(sw_name)
                    #set devices
                self.dds_list[name] = {'device': self.get_device(name),
                                       'chip_sel': args['chip_select'],
                                       'cpld': cpld_dev,
                                       'switch': sw_dev}
            elif params['class'] == 'CPLD':
                #get urukul component names and devices
                args = params['arguments']
                    #get io-update switch
                update_name = args['io_update_device']
                update_dev = self.get_device(update_name)
                self.urukul_list[cpld_name] = {'device': self.get_device(cpld_name),
                                               'update': self.get_device(update_dev),
                                               'clk': args['refclk']}
        #todo: do DAC and ADC


    def _setVariables(self):
        #sequencer variables
        self.numRuns = 0
        self.maxRuns = 0
        #pmt variables
        self.pmtInterval = 0
        self.pmtMode = 0 #0 is normal/automatic, 1 is differential
        self.pmtArrayLength = 10000
        self.setattr_dataset('PMT_count', np.full(self.pmtArrayLength, np.nan))
        #linetrigger variables
        self.linetrigger_delay = 0 * us
        self.linetrigger_active = False

    @kernel
    def _initializeDevices(self):
        #initialize devices
            #set ttlinout devices to be input
        for component_list in self.ttlin_list.values():
            component_list['device'].input()
            #initialize DDSs
        for component_list in self.dds_list.values():
            component_list['device'].init()
        for component_list in self.urukul_list.values():
            component_list['device'].init()
        #todo: set attenuator, etc

    #Sequence functions
    @kernel(flags = {"fast-math"})
    def programSequence(self, ttl_sequence, dds_single_sequence, dds_ramp_sequence):
        PMT_device = self.ttlin_list['PMT']
        #record pulse sequence in memory
        with self.core_dma.record("pulse_sequence"):
            #program ttl sequence
            for timestamp, ttlCommandArr in ttl_sequence:
                at_mu(timestamp)
                with parallel:
                    #todo: convert to name format
                    for i in range(ttl_sequence.channelTotal):
                        if ttlCommandArr[i] == 1:
                            self.ttlout_list[i].on()
                        elif ttlCommandArr[i] == -1:
                            self.ttlout_list[i].off()
            #program DDS sequence
            for timestamp, params in dds_single_sequence:

            #program DDS Ramp
            #program PMT input
            for i in range():
                time_pmt = PMT_device.gate_rising_mu(self.pmtInterval)
                counts_pmt = PMT_device.count(time_pmt)
                self.mutate_dataset(self.PMT_count, i, counts_pmt)
            #todo: program dds
            #todo: program ttls for dds's


    @kernel
    def runSequence(self, runs):
        self.core.reset()
        self.maxRuns = runs

        #get sequence handle to minimize overhead
        sequence_handle = self.core_dma.get_handle("pulse_sequence")

        #wait until line trigger receives input or we disable the line trigger
        while self.linetrigger_active:
            #wait in blocks of 10ms
            time_gate = self.ttlin_list['LineTrigger'].gate_rising_mu(10 * ms)
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
        #todo: process data

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
        #todo:

    @kernel
    def setManual(self, channel, state):
        '''
        Set the logic of the TTL to be manual or not
        '''
        if state:
            self.ttlout_list[channel].on()
        else:
            self.ttlout_list[channel].on()

    #PMT functions
    def setMode(self, mode):
        """
        User selects PMT counting rate
        """
        self.pmtMode = mode

    def setPMTCountInterval(self, time):
        '''
        Set count rate of PMT in us
        '''
        self.pmtInterval = time

    def getReadoutCounts(self, number):
        '''
        Get the readout count data.
        '''
        #todo: remove np.nan
        return self.PMT_count

    def resetReadoutCounts(self):
        '''
        Reset the FIFO on the FPGA for the read-out count.
        '''
        self.set_dataset('PMT_count', np.full(self.pmtArrayLength, np.nan))

    #DDS functions
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

    @kernel
    def setDDSParam(self, chan, _asf, _ftw, _pow):
        self.dds_list[chan].set_mu(ftw = _ftw, asf = _asf, pow = _pow)

    @kernel
    def setDDSSingle(self, chan, addr_start, addr_stop, data, _profile):
        #todo: cpld set profile
        self.dds_list[chan].set_profile_ram(addr_start, addr_stop, profile = _profile)
        self.dds_list[chan].write_ram(data)

    @kernel
    def setDDSRAM(self, chan, addr_start, addr_stop, data, _profile):
        #todo: cpld set profile
        self.dds_list[chan].set_profile_ram(addr_start, addr_stop, profile = _profile)
        self.dds_list[chan].write_ram(data)

    @kernel
    def toggleDDS(self, dds, state):
        '''
        Turn the DDS on/off.
        '''
        self.dds_list[dds].cfg_sw(state)

    @kernel
    def resetAllDDS(self):
        '''
        Reset the ram position of all dds chips to 0
        '''
        pass

    @kernel
    def advanceAllDDS(self):
        '''
        Advance the ram position of all dds chips
        '''
        pass

    #LineTrigger functions
    def enableLineTrigger(self, delay = 0):
        '''
        Enable line trigger with some delay (in machine units)
        '''
        self.linetrigger_active = True
        self.linetrigger_delay = delay

    def disableLineTrigger(self):
        '''
        Disable the line trigger
        '''
        self.linetrigger_active = False

