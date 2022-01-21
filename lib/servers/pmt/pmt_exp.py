from artiq.experiment import *
from datetime import datetime
from numpy import zeros


class PMT_experiment(EnvExperiment):
    """
    Programs a PMT recording sequence onto ARTIQ.
    """

    def build(self):
        # get core devices
        self.setattr_device('core')
        self.setattr_device('core_dma')
        # set arguments
        self.setattr_argument('ttl_number', NumberValue(ndecimals=0, step=1, min=0, max=23))
        self.setattr_argument('trigger_ttl_number', NumberValue(default=-1, ndecimals=0, step=1, min=-1, max=23))
        self.setattr_argument('bin_time_us', NumberValue(default=10, ndecimals=0, step=1, min=1, max=100))
        self.setattr_argument('reset_time_us', NumberValue(default=10, ndecimals=0, step=1, min=1, max=100))
        self.setattr_argument('length_us', NumberValue(default=1000, ndecimals=0, step=1, min=1, max=10000))
        self.setattr_argument('edge_method', StringValue(default='rising'))

    def prepare(self):
        # get ttl device
        self.ttl_input = self.get_device('ttl_{:d}'.format(self.ttl_number)
        self.trigger_input = self.get_device('ttl_{:d}'.format(self.trigger_ttl_number)
        # ensure ttls are inout
        if (self.ttl_input.__class__.__name__ != 'TTLInOut') or (self.trigger_input.__class__.__name__ != 'TTLInOut'):
            raise Exception('Error: TTLs are output-only.')
        # get edge gating method
        if self.edge_method == 'rising':
            self.gate_edge = self.ttl_input.gate_rising_mu
        elif self.edge_method == 'falling':
            self.gate_edge = self.ttl_input.gate_falling_mu
        elif self.edge_method == 'both':
            self.gate_edge = self.ttl_input.gate_both_mu
        # create dataset
        self.num_bins = int(self.get_argument('length_us') / self.get_argument('bin_time_us'))
        date = datetime.now()
        self.dataset_name = 'pmt_{0:s}_{1:s}_{2:02d}_{0:s}_{1:02d}:{2:02d}'.format(str(date.year), date.month,
                                                                                   date.day, date.hour, date.minute)
        self.set_dataset(self.dataset_name, zeros(self.num_bins), persist=True)
        # set time variables in mu
        self.bin_time_mu = self.core.seconds_to_mu(self.bin_time_ms * us)
        self.reset_time_mu = self.core.seconds_to_mu(self.reset_time_us * us)
        self.length_mu = self.core.seconds_to_mu(self.length_us * us)

    @kernel
    def run(self):
        # record pulse sequence in memory
        self.core.reset()
        with self.core_dma.record("PMT_exp"):
            # set TTLs to input
            self.core.reset()
            self.ttl_input.input()
            self.trigger_input.input()
            # wait for linetrigger if active
            if self.trigger_ttl_number != -1:
                while True:
                    trigger_active = self.trigger_input.gate_rising(10 * us)
                    if (self.trigger_input.count(trigger_active) > 0):
                        break
            # start at t=0
            at_mu(0)
            for i in range(self.num_bins):
                gate_end_mu = self.gate_edge_mu(self.bin_time_mu)
                delay_mu(self.reset_time_mu)
                self.mutate_dataset(self.dataset_name, i, self.ttl_input.count(gate_end_mu))
        # get playback handle
        handle = self.core_dma.get_handle("PMT_exp")
        #todo: test
        #todo: return dma handle
