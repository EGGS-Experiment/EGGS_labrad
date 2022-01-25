from artiq.experiment import *
from datetime import datetime
from numpy import zeros


class PMT_experiment(EnvExperiment):
    """
    Programs a PMT recording sequence onto ARTIQ.
    """

    def build(self):
        # get arguments
        self.setattr_argument('ttl_number', NumberValue(ndecimals=0, step=1, min=0, max=23))
        self.setattr_argument('trigger_ttl_number', NumberValue(default=-1, ndecimals=0, step=1, min=-1, max=23))
        self.setattr_argument('bin_time_us', NumberValue(default=10, ndecimals=0, step=1, min=1, max=100))
        self.setattr_argument('reset_time_us', NumberValue(default=100, ndecimals=0, step=1, min=1, max=100))
        self.setattr_argument('length_us', NumberValue(default=1000, ndecimals=0, step=1, min=1, max=100000))
        self.setattr_argument('edge_method', StringValue(default='rising'))
        # get core devices
        self.setattr_device('core')
        self.setattr_device('core_dma')

    def prepare(self):
        # get ttl input
        pmt_name = 'ttl{:d}'.format(self.ttl_number)
        self.ttl_input = self.get_device(pmt_name)
        # get trigger input
        trigger_name = 'ttl{:d}'.format(self.trigger_ttl_number)
        if self.trigger_ttl_number != -1:
            self.trigger_input = self.get_device(trigger_name)
        else:
            self.trigger_input = self.ttl_input
        # check TTLs are input
        if (self.ttl_input.__class__.__name__ != 'TTLInOut') or (self.trigger_input.__class__.__name__ != 'TTLInOut'):
            raise Exception('Error: TTLs are output-only.')
        # check edge gating input valid
        if self.edge_method not in ('rising', 'falling', 'both'):
            raise Exception('Error: invalid edge method.')
        # get edge gating method
        if self.edge_method == 'rising':
            self.gate_edge = getattr(self.ttl_input, 'gate_rising_mu')
        elif self.edge_method == 'falling':
            self.gate_edge = getattr(self.ttl_input, 'gate_falling_mu')
        elif self.edge_method == 'both':
            self.gate_edge = getattr(self.ttl_input, 'gate_both_mu')
        # process input values into mu
        self.bin_time_mu = self.core.seconds_to_mu(self.bin_time_us * us)
        self.reset_time_mu = self.core.seconds_to_mu(self.reset_time_us * us)
        self.length_mu = self.core.seconds_to_mu(self.length_us * us)
        # composite values
        self.total_edges = 0
        self.num_bins = int(self.length_us / (self.bin_time_us + self.reset_time_us))
        # create dataset
        date = datetime.now()
        self.dataset_name = 'pmt_{:s}_{:02d}_{:02d}_{:02d}{:02d}'.format(str(date.year), date.month, date.day,
                                                                         date.hour, date.minute)
        self.set_dataset(self.dataset_name, zeros(self.num_bins), broadcast=True)
        self.setattr_dataset(self.dataset_name)
        # print values
        print('bin time (us):', self.bin_time_us)
        print('reset time (us):', self.reset_time_us)
        print('length (us):', self.length_us)
        print('bins:', self.num_bins)

    # todo: get minimum bin times for exp vs dma
    # minimum for exp is 100us reset
    # todo: do dma

    @kernel
    def run(self):
        self.core.reset()
        self.ttl_input.input()
        self.trigger_input.input()
        self.core.break_realtime()
        for i in range(self.num_bins):
            self.mutate_dataset(self.dataset_name, i, self.ttl_input.count(self.gate_edge(self.bin_time_mu)))
            delay_mu(self.reset_time_mu)

        # # record pulse sequence in memory
        # self.core.reset()
        # with self.core_dma.record("PMT_exp"):
        #     # set TTLs to input
        #     self.core.reset()
        #     self.ttl_input.input()
        #     self.trigger_input.input()
        #     # wait for linetrigger if active
        #     if self.trigger_ttl_number != -1:
        #         while True:
        #             trigger_active = self.trigger_input.gate_rising(10 * us)
        #             if (self.trigger_input.count(trigger_active) > 0):
        #                 break
        #     # start at t=0
        #     at_mu(0)
        #     for i in range(self.num_bins):
        #         gate_end_mu = self.gate_edge_mu(self.bin_time_mu)
        #         delay_mu(self.reset_time_mu)
        #         self.mutate_dataset(self.dataset_name, i, self.ttl_input.count(gate_end_mu))
        # # get playback handle
        # handle = self.core_dma.get_handle("PMT_exp")

    def analyze(self):
        print('edges:', self.total_edges)

        #todo: return dma handle
