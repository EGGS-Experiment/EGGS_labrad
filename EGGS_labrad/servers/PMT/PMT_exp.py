from numpy import zeros
from datetime import datetime
from artiq.experiment import *

_DMA_HANDLE = 'PMT_exp'
_DATASET_NAME = 'pmt_test_dataset'


class PMT_experiment2(EnvExperiment):
    """
    Programs a PMT recording sequence onto ARTIQ.
    Draft 2.
    """

    def build(self):
        # ttls
        self.setattr_argument('signal_ttl', NumberValue(ndecimals=0, step=1, min=0, max=3))
        self.setattr_argument('power_ttl', NumberValue(ndecimals=0, step=1, min=4, max=23))
        #self.setattr_argument('overlight_ttl', NumberValue(ndecimals=0, step=1, min=0, max=3))
        self.setattr_argument('trigger_ttl', NumberValue(default=1, ndecimals=0, step=1, min=-1, max=23))
        self.setattr_argument('trigger_status', BooleanValue(default=False))
        # timing
        self.setattr_argument('time_bin_us', NumberValue(default=0.1, ndecimals=3, step=1, min=0.01, max=100))
        self.setattr_argument('time_reset_us', NumberValue(default=0.1, ndecimals=3, step=1, min=0, max=100))
        self.setattr_argument('time_total_us', NumberValue(default=1, ndecimals=3, step=1, min=0.01, max=1000))
        # edge method
        self.setattr_argument('edge_method', StringValue(default='rising'))
        # get core devices
        self.setattr_device('core')
        self.setattr_device('core_dma')

    def prepare(self):
        # get TTLs
        self.ttl_signal = self.get_device('ttl{:d}'.format(self.signal_ttl))
        self.ttl_power = self.get_device('ttl{:d}'.format(self.power_ttl))
        #self.ttl_overlight = self.get_device('ttl{:d}'.format(self.overlight_ttl))
        if self.trigger_status:
            self.ttl_trigger = self.get_device('ttl{:d}'.format(self.trigger_ttl))
        else:
            self.ttl_trigger = self.ttl_signal

        # check TTLs are input
        if (self.ttl_signal.__class__.__name__ != 'TTLInOut') or (self.ttl_trigger.__class__.__name__ != 'TTLInOut'):
            raise Exception('Error: TTLs must be input.')
        # check linetrigger and PMT are on different TTLs
        elif self.trigger_status and (self.ttl_signal == self.ttl_trigger):
            raise Exception('Error: Trigger and PMT TTLs cannot be the same.')
        # check edge gating input valid
        elif self.edge_method not in ('rising', 'falling', 'both'):
            raise Exception('Error: invalid edge method.')

        # get edge gating method
        self.gate_edge = getattr(self.ttl_signal, 'gate_{:s}_mu'.format(self.edge_method))

        # convert input values into mu
        self.time_bin_mu = self.core.seconds_to_mu(self.time_bin_us * us)
        self.time_reset_mu = self.core.seconds_to_mu(self.time_reset_us * us)
        self.time_total_mu = self.core.seconds_to_mu(self.time_total_us * us)
        # create dataset
        #date = datetime.now()
        #self.dataset_name = 'pmt_{:s}_{:02d}_{:02d}_{:02d}:{:02d}'.format(str(date.year), date.month, date.day,
        #                                                                  date.hour, date.minute)
        self.dataset_name = _DATASET_NAME
        self.num_bins = int(self.time_total_us / (self.time_bin_us + self.time_reset_us))
        self.set_dataset(self.dataset_name, zeros(self.num_bins), broadcast=True)
        self.setattr_dataset(self.dataset_name)

    @kernel
    def run(self):
        self.core.reset()
        # set TTLs to correct direction
        self.ttl_signal.input()
        self.ttl_trigger.input()
        self.core.break_realtime()

        # turn on power to PMT
        self.ttl_power.on()
        delay(600 * us)

        # record DMA sequence
        with self.core_dma.record(_DMA_HANDLE):
            # todo: implement overlight
            # read overlight
            # stop if overlight
            # todo: implement linetrigger
            # wait for linetrigger if active
            #     if self.ttl_trigger != -1:
            #         while True:
            #             trigger_active = self.trigger_input.gate_rising(10 * us)
            #             if (self.trigger_input.count(trigger_active) > 0):
            #                 break
            self.core.break_realtime()
            for i in range(self.num_bins):
                self.core.break_realtime()
                self.mutate_dataset(self.dataset_name, i, self.ttl_signal.count(self.gate_edge(self.time_bin_mu)))
                delay_mu(self.time_reset_mu)
        self.core.break_realtime()

    def analyze(self):
        th1 = self.get_dataset(self.dataset_name)
        print(th1)
