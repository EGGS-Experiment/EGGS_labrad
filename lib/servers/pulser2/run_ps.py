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
        try:
            for i in range(self.maxRuns):
                try:
                    self.core.reset()
                    self.core_dma.playback_handle(handle)
                    self.numRuns += 1
                except RTIOUnderflow:
                    self.core.reset()
                    continue
        except TerminationRequested:
            self.set_dataset('numRuns', self.numRuns, broadcast=True)
            print('Pulse Sequence Stopped')
        self.set_dataset('numRuns', self.numRuns, broadcast = True)
        print('Pulse Sequence Finished')
