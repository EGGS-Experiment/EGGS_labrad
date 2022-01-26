from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager, DatasetManager

# import numpy as np


class ARTIQ_api(object):
    """
    An API for the ARTIQ box.
    Directly accesses the hardware on the box without having to use artiq_master.
    """

    def __init__(self):
        self.devices = DeviceDB('C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db_2.py')
        self.device_manager = DeviceManager(self.devices)
        self._getDevices()
        self._initializeDevices()


    # SETUP
    def _getDevices(self):
        # get core
        self.core = self.device_manager.get("core")
        self.core_dma = self.device_manager.get("core_dma")

        # store devices in dictionary where device name is key
        # and device itself is value
        self.device_db = self.devices.get_device_db()
        self.ttlout_list = {}
        self.ttlin_list = {}
        self.dds_list = {}
        self.urukul_list = {}
        self.zotino = None
        self.fastino = None
        self.sampler = None
        self.phaser = None

        # assign names and devices
        for name, params in self.device_db.items():
            # only get devices with named class
            if 'class' not in params:
                continue
            # set device as attribute
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
                self.zotino = device
            elif devicetype == 'Fastino':
                self.fastino = device
            elif devicetype == 'Sampler':
                self.sampler = device

    def _initializeDevices(self):
        """
        Initialize devices that need to be initialized.
        """
        # initialize DDSs
        self.initializeDDSAll()
        # one-off device init
        self.initializeDAC()


    # PULSE SEQUENCING
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
        # TTL
        ttl_times = list(ttl_seq.keys())
        ttl_commands = list(ttl_seq.values())
        # DDS
        dds_times = list(dds_seq.keys())
        dds_commands = list(dds_seq.values())
        # send to kernel
        self._record(ttl_times, ttl_commands, dds_times, dds_commands, sequencename)

    @kernel
    def eraseSequence(self, sequencename):
        """
        Erase the given pulse sequence from DMA.
        """
        self.core.reset()
        self.core_dma.erase(sequencename)


    # DMA
    def runDMA(self, handle_name):
        handle = self.core_dma.get_handle(handle_name)
        self._runDMA(handle)

    @kernel
    def _runDMA(self, handle):
        self.core.reset()
        self.core_dma.playback_handle(handle)
        self.core.reset()


    # TTL
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


    # DDS/URUKUL
    def initializeDDSAll(self):
        # initialize urukul cplds as well as dds channels
        device_list = list(self.urukul_list.values())
        device_list.extend(list(self.dds_list.values()))
        for device in device_list:
            self._initializeDDS(device)

    def initializeDDS(self, dds_name):
        dev = self.dds_list[dds_name]
        self._initializeDDS(dev)

    @kernel
    def _initializeDDS(self, dev):
        self.core.reset()
        dev.init()

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
        dev.set_att_mu(att_mu)

    def readDDS(self, dds_name, reg, length):
        """
        Read the value of a DDS register.
        """
        dev = self.dds_list[dds_name]
        if length == 16:
            return self._readDDS16(dev, reg)
        elif length == 32:
            return self._readDDS32(dev, reg)
        elif length == 64:
            return self._readDDS64(dev, reg)

    @kernel
    def _readDDS16(self, dev, reg):
        self.core.reset()
        return dev.read16(reg)

    @kernel
    def _readDDS32(self, dev, reg):
        self.core.reset()
        return dev.read32(reg)

    @kernel
    def _readDDS64(self, dev, reg):
        self.core.reset()
        return dev.read64(reg)


    # DAC/ZOTINO
    @kernel
    def initializeDAC(self):
        """
        Initialize the DAC.
        """
        self.core.reset()
        self.zotino.init()

    @kernel
    def setDAC(self, channel_num, volt_mu):
        """
        Set the voltage of a DAC register.
        """
        self.core.reset()
        self.zotino.write_dac_mu(channel_num, volt_mu)
        self.zotino.load()

    @kernel
    def setDACGain(self, channel_num, gain_mu):
        """
        Set the gain of a DAC channel.
        """
        self.core.reset()
        self.zotino.write_gain_mu(channel_num, gain_mu)
        self.zotino.load()

    @kernel
    def setDACOffset(self, channel_num, volt_mu):
        """
        Set the voltage of a DAC offset register.
        """
        self.core.reset()
        self.zotino.write_offset_mu(channel_num, volt_mu)
        self.zotino.load()

    @kernel
    def setDACGlobal(self, word):
        """
        Set the OFSx registers on the AD5372.
        """
        self.core.reset()
        self.zotino.write_offset_dacs_mu(word)

    @kernel
    def readDAC(self, channel_num, address):
        """
        Read the value of one of the DAC registers.
        :param channel_num: Channel to read from
        :param address: Register to read from
        :return: the value of the register
        """
        self.core.reset()
        reg_val = self.zotino.read_reg(channel_num, address)
        return reg_val


    # FASTINO
    @kernel
    def initializeFastino(self):
        """
        Initialize the Fastino.
        """
        self.core.break_realtime()
        self.fastino.init()

    @kernel
    def setFastino(self, channel_num, volt_mu):
        """
        Set the voltage of a Fastino register.
        """
        self.core.break_realtime()
        self.fastino.write_dac_mu(channel_num, volt_mu)
        self.fastino.load()
        self.core.break_realtime()
        self.fastino.write(channel_num, volt_mu)

    @kernel
    def readFastino(self, addr):
        self.core.break_realtime()
        return self.fastino.read(addr)

    @kernel
    def continuousFastino(self, channel_mask):
        """
        Allowed a Fastino channel to be updated continuously regardless of incoming data.
        """
        self.core.break_realtime()
        self.fastino.set_continuous(channel_mask)

    # todo: fastino interpolating/CIC


    # SAMPLER
    @kernel
    def initializeSampler(self):
        """
        Initialize the Sampler.
        """
        self.core.reset()
        self.sampler.init()

    @kernel
    def setSamplerGain(self, channel_num, gain_mu):
        """
        Set the gain for a sampler channel.
        :param channel_num: Channel to set
        :param gain_mu: Register to read from
        :return: the value of the register
        """
        self.core.reset()
        self.sampler.set_gain_mu(channel_num, gain_mu)

    @kernel
    def getSamplerGains(self):
        """
        Get the gain of all sampler channels.
        :return: the sample channel gains.
        """
        self.core.reset()
        return self.sampler.get_gains_mu()

    @kernel
    def readSampler(self, sampleArr):
        """
        Set the gain of
        :param channel_num: Channel to set
        :param gain_mu: Register to read from
        :return: the value of the register
        """
        self.core.reset()
        return self.sampler.sample_mu(sampleArr)

#todo: phaser
#todo: try and speed up some functions by going more machine level
#todo: try using break_realtime() instead of reset