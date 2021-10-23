from artiq.experiment import *

class pulse_sequence(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        self.setattr_device('core_dma')
        #self.setattr_argument("maxRuns", NumberValue(ndecimals=0, step=1))
        self.numRuns = 0
        self.maxRuns = 10

    @kernel
    def run(self):
        handle = self.core_dma.get_handle('ps')
        self.core.reset()
        for i in range(self.maxRuns):
            self.core.reset()
            self.core_dma.playback_handle(handle)
        print('finished')
