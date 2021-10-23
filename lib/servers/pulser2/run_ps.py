from artiq.experiment import *
import numpy as np

class pulse_sequence(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        self.setattr_device('core_dma')
        self.setattr_argument("maxRuns", NumberValue(ndecimals=0, step=1, type = 'int'))
        self.numRuns = 0
        self.set_dataset('numRuns', np.array([0]), broadcast = True)

    @kernel
    def run(self):
        handle = self.core_dma.get_handle('default')
        self.core.reset()
        while self.numRuns < self.maxRuns:
            self.core.reset()
            self.core_dma.playback_handle(handle)
            self.numRuns += 1
            self.mutate_dataset('numRuns', 0, self.numRuns)
        print('Pulse Sequence Finished')
