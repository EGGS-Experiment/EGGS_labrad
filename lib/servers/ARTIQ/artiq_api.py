import numpy as np

from sipyco.pc_rpc import Client
from asyncio import get_event_loop()

from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager, DatasetManager
from artiq.master.worker_impl import CCB, Scheduler

class api(object):
    def __init__(self):
        self.core=core

    @kernel
    def on(self):
        core.reset()
        ttl4.on()
        print('thkim')

api_obj=api()
api_obj.on()

class ARTIQ_api(object):
    """
    An API for the ARTIQ box.
    Directly accesses the hardware on the box without having to use artiq_master.
    """

    def __init__(self):
        self.devices = DeviceDB('C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db.py')
        self.device_manager = DeviceManager(self.devices)
        self._getDevices()
        self._setVariables()

    #Setup functions
    def _getDevices(self):
        #get core
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("scheduler")

        #get device names
        self.device_db = self.get_device_db()
            #create holding lists (dict not supported in kernel methods)
        self.ttlout_list = list()
        self.ttlin_list = list()
        self.dds_list = list()
        self.urukul_list = list()
        self.adc = None
        self.dac = None

        #assign names and devices
        for name, params in self.device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            #set device as attribute
            devicetype = params['class']
            device = self.get_device(name)
            self.setattr_device(name)
            if devicetype == 'TTLInOut':
                self.ttlin_list.append(device)
            elif devicetype == 'TTLOut':
                if 'pmt' in name:
                    self.pmt_list.append(device)
                elif 'linetrigger' in name:
                    self.linetrigger_list.append(device)
                elif 'urukul' not in name:
                    self.ttlout_list.append(device)
            elif devicetype == 'AD9910':
                self.dds_list.append(device)
            elif devicetype == 'CPLD':
                self.urukul_list.append(device)
            elif devicetype == 'Zotino':
                self.dac = device
            elif devicetype == 'Sampler':
                self.adc = device
            elif devicetype == 'Grabber':
                self.camera = device

    def initializeDevices(self):
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
        self.adc.init()
        self.core.reset()

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
    @kernel
    def setTTL(self, ttlnum, state):
        """
        Manually set the state of a TTL.
        """
        self.core.reset()
        if state:
            self.ttlout_list[ttlnum].on()
        else:
            self.ttlout_list[ttlnum].off()

    #DDS functions
    @kernel
    def initializeDDS(self):
        '''
        Initialize all DDSs
        '''
        self.core.reset()
        for device in self.dds_list:
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        self.core.reset()

        #reset urukul cpld
        for device in self.urukul_list:
            try:
                device.init()
            except RTIOUnderflow:
                self.core.break_realtime()
                device.init()
        self.core.reset()

    @kernel
    def toggleDDS(self, ddsnum, state):
        """
        Toggle a DDS using the RF switch.
        """
        self.dds_list[ddsnum].cfg_sw(state)

    @kernel
    def setDDS(self, ddsnum, params, _profile):
        """
         Manually set the state of a DDS.
         """
        _ftw = params[0]
        _asf = params[1]
        _pow = params[2]
        self.dds_list[ddsnum].set_mu(ftw = _freq, asf = _ampl, pow = _pow, profile = _profile)
        #todo: do we need to change profile to desired one?

    @kernel
    def setDAC(self, channel, voltage):
        self.dac.set_dac_mu([voltage], channels=[channel])