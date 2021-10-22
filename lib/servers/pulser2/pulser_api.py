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

    def prepare(self):
        pass

    def run(self):
        util.runServer(Pulser_server(self))

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

