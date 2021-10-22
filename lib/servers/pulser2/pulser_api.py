from artiq.experiment import *
import numpy as np

from artiq.language.environment import ProcessArgumentManager
from artiq.master.worker_db import DeviceManager, DatasetManager
from artiq.master.worker_impl import ParentDeviceDB, ParentDatasetDB, CCB, Scheduler

from artiq.language.types import TInt32, TInt64, TStr, TNone, TTuple

from pulser_server import Pulser_server
from labrad import util


# device_mgr = DeviceManager(ParentDeviceDB, virtual_devices={"scheduler": Scheduler(), "ccb": CCB()})
# dataset_mgr = DatasetManager(ParentDatasetDB)
# argument_mgr = ProcessArgumentManager([])

class Pulser_api(EnvExperiment):
    """
    Pulser api
    """

    def build(self):
        self.setattr_device('core')
        self.setattr_device('core_dma')
        self.setattr_device('scheduler')
        self.setattr_device('ttl4')
        self.setattr_device('ttl5')
        self.setattr_device('urukul0_cpld')
        self.setattr_device('urukul0_ch0')
        self.maxRuns = 0
        self.numRuns = 0

        #get devices
        self._getDevices()
        #need to config hardware as well


    def prepare(self):
        pass

    def run(self):
        util.runServer(Pulser_server(self))

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
            devicetype = params['class']
            if devicetype == 'TTLInOut':
                self.ttlin_list[name] = self.get_device(name)
            elif devicetype == 'TTLOut':
                if 'pmt' in name:
                    self.pmt_list[name] = self.get_device(name)
                elif 'linetrigger' in name:
                    self.linetrigger_list[name] = self.get_device(name)
                elif 'urukul' not in name:
                    self.ttlout_list[name] = self.get_device(name)
            elif devicetype == 'AD9910':
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
            elif devicetype == 'CPLD':
                #get urukul component names and devices
                args = params['arguments']
                    #get io-update switch
                update_name = args['io_update_device']
                update_dev = self.get_device(update_name)
                self.urukul_list[cpld_name] = {'device': self.get_device(cpld_name),
                                               'update': self.get_device(update_dev),
                                               'clk': args['refclk']}

    def _setVariables(self):
        """
        Set up internal variables
        """
        #sequencer variables
        self.numRuns = 0
        self.maxRuns = 0
        #pmt variables
        self.pmtInterval = 0
        self.pmtMode = 0 #0 is normal/automatic, 1 is differential
        self.pmtArrayLength = 10000
        #linetrigger variables
        self.linetrigger_delay = 0
        self.linetrigger_active = False

    #@rpc(flags = {'async'})
    def printlog(self, text):
        print('msg: ' + str(text))

    @kernel
    def _initializeDevices(self):
        pass
        # self.urukul0_cpld.init()
        # self.urukul0_ch0.init()
        # self.urukul0_ch0.cfg_sw(1)

    @kernel
    def _record(self):
        with self.core_dma.record('ps'):
            for i in range(400):
                with parallel:
                    self.ttl4.pulse(1*ms)
                    self.ttl5.pulse(1*ms)
                delay(1.0*ms)

    @kernel
    def _runSequence(self, _maxruns):
        try:
            handle = self.core_dma.get_handle('ps')
            self.maxRuns = _maxruns
            self.core.reset()
            while self.numRuns < self.maxRuns:
                self.core_dma.playback_handle(handle)
                self.numRuns += 1
                self.core.reset()
            self.maxRuns = 0
        except Exception as e:
            raise

    @kernel
    def _stopSequence(self):
        #self.maxRuns = 0
        self.core_dma.erase('ps')
        self.printlog(self.numRuns)
        self.printlog('stop success')

