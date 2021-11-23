import numpy as np

from sipyco.pc_rpc import Client
from asyncio import get_event_loop

from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager, DatasetManager
from artiq.master.worker_impl import CCB, Scheduler

class ARTIQ_api(object):
    """
    An API for the ARTIQ box.
    Directly accesses the hardware on the box without having to use artiq_master.
    """

    def __init__(self):
        self.devices = DeviceDB('C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db.py')
        self.device_manager = DeviceManager(self.devices)
        self._getDevices()
        #self._initializeDevices()

    #Setup functions
    def _getDevices(self):
        #get core
        self.core = self.device_manager.get("core")
        self.core_dma = self.device_manager.get("core_dma")

        #get device names
        self.device_db = self.devices.get_device_db()
            #create holding lists (dict not supported in kernel methods)
        self.ttlout_list = {}
        self.ttlin_list = {}
        self.dds_list = {}
        self.urukul_list = {}
        self.dac = None

        #assign names and devices
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            #set device as attribute
            devicetype = params['class']
            device = self.device_manager.get(name)
            if devicetype == 'TTLInOut':
                self.ttlin_list[name] = device
            elif devicetype == 'TTLOut':
                self.ttlout_list[name] = device
            elif devicetype == 'AD9910':
                self.dds_list[name] = device
            elif devicetype == 'CPLD':
                self.urukul_list[name] = device
            elif devicetype == 'Zotino':
                self.dac = device

    def _initializeDevices(self):
        """
        Initialize devices that need to be initialized.
        """
        #set ttlinout devices to be input
        self.core.reset()
        for device in self.ttlin_list:
            try:
                device.input()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.input()
        #initialize DDSs
        for component_list in self.dds_list.values():
            self.core.break_realtime()
            component_list['device'].init()
        for component_list in self.urukul_list.values():
            self.core.break_realtime()
            component_list['device'].init()
        #one-off device init
        self.dac.init()
        self.core.reset()

    #Pulse sequencing
    @kernel
    def record(self, sequencename):
        self.core.reset()
        with self.core_dma.record(sequencename):
            for i in range(50):
                with parallel:
                    self.ttlout_list[0].pulse(1*ms)
                    self.ttlout_list[1].pulse(1*ms)
                delay(1.0*ms)

    def record2(self, ttl_seq, dds_seq, sequencename):
        """
        Processes the TTL and DDS sequence into a format
        more easily readable and processable by ARTIQ.
        """
        #TTLs
        ttl_times = list(ttl_seq.keys())
        ttl_commands = list(ttl_seq.values())
        #DDSs
        dds_times = list(dds_seq.keys())
        dds_commands = list(dds_seq.values())
        #send to kernel
        self._record(ttl_times, ttl_commands, dds_times, dds_commands, sequencename)

    @kernel
    def eraseSequence(self, sequencename):
        """
        Erase the given pulse sequence from DMA.
        """
        self.core.reset()
        self.core_dma.erase(sequencename)

    #TTL functions
    def setTTL(self, ttlname, state):
        """
        Manually set the state of a TTL.
        """
        try:
            dev = self.ttlout_list[ttlname]
        except KeyError:
            raise Exception('Invalid device name.')
        self._setTTL(dev, state)

    @kernel
    def _setTTL(self, dev, state):
        self.core.reset()
        if state:
            dev.on()
        else:
            dev.off()


    #DDS functions
    @kernel
    def initializeDDSAll(self, dds_name):
        '''
        Initialize all DDSs.
        '''
        self.core.reset()
        #reset urukul cpld
        for device in self.urukul_list:
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        #reset each DDS channel
        self.core.reset()
        for device in self.dds_list:
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()

    def initializeDDS(self, dds_name):
        dev = self.dds_list[dds_name]
        self._initializeDDS(dev)

    @kernel
    def _initializeDDS(self, dev):
        self.core.reset()
        self.dev.init()

    def toggleDDS(self, dds_name, state):
        """
        Toggle a DDS using the RF switch.
        """
        dev = self.dds_list[dds_name]
        self._toggleDDS(dev, state)

    @kernel
    def _toggleDDS(self, dev, state):
        self.core.reset()
        dev.cfg_sw(state)

    def setDDS(self, dds_name, param, val):
        """
        Manually set the state of a DDS.
        """
        dev = self.dds_list[dds_name]
        if param == 0:
            self._setDDSFreq(dev, val)
        elif param == 1:
            self._setDDSAmpl(dev, val)
        elif param == 2:
            self._setDDSPhase(dev, val)

    @kernel
    def _setDDSFreq(self, dev, ftw):
        self.core.reset()
        dev.set_ftw(ftw)

    @kernel
    def _setDDSAmpl(self, dev, asf):
        self.core.reset()
        dev.set_asf(asf)

    @kernel
    def _setDDSPhase(self, dev, pow):
        self.core.reset()
        dev.set_pow(pow)

    def setDDSAtt(self, dds_name, att_mu):
        """
        Set the DDS attenuation.
        """
        dev = self.dds_list[dds_name]
        self._setDDSAtt(dev, att_mu)

    @kernel
    def _setDDSAtt(self, dev, att_mu):
        self.core.reset()
        #dev.set_att_mu(att)
        dev.set_att(att)


    #DAC functions
    @kernel
    def initializeDAC(self):
        """
        Initialize the DAC.
        """
        self.core.reset()
        self.dac.init()

    @kernel
    def setDAC(self, channel_num, volt_mu):
        """
        Set the voltage of a DAC register.
        """
        self.core.reset()
        self.dac.write_dac_mu(channel_num, volt_mu)
        self.dac.load()

    @kernel
    def setDACGain(self, channel_num, gain_mu):
        """
        Set the gain of a DAC channel.
        """
        self.core.reset()
        self.dac.write_gain_mu(channel_num, gain_mu)
        self.dac.load()

    @kernel
    def setDACOffset(self, channel_num, volt_mu):
        """
        Set the voltage of a DAC offset register.
        """
        self.core.reset()
        self.dac.write_offset_mu(channel_num, volt_mu)
        self.dac.load()

    @kernel
    def setDACGlobalOffset(self, word):
        """
        Set the OFSx registers on the AD5372.
        """
        self.core.reset()
        self.dac.write_offset_dacs_mu(word)