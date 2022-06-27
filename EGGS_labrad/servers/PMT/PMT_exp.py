from numpy import zeros
from artiq.experiment import *

_DMA_HANDLE = 'PMT_exp'
_DATASET_NAME = 'pmt_test_dataset'

# todo: implement overlight
# todo: implement linetrigger


class PMT_experiment(EnvExperiment):
    """
    Programs and runs a PMT recording sequence onto ARTIQ.
    """

    def build(self):
        """
        Set devices and arguments for the experiment.
        """
        self.setattr_device("core")
        self.setattr_device("core_dma")

        # experiment runs
        self.setattr_argument("repetitions", NumberValue(default=1000, ndecimals=0, step=1, min=1, max=1000))

        # timing
        self.setattr_argument('time_bin_us', NumberValue(default=500, ndecimals=3, step=1, min=0.01, max=100))
        self.setattr_argument('time_reset_us', NumberValue(default=100, ndecimals=3, step=1, min=0, max=100))

        # PMT
        self.setattr_argument("pmt_input_channel",      NumberValue(default=0, ndecimals=0, step=1, min=0, max=3))
        self.setattr_argument("pmt_power_channel",      NumberValue(default=0, ndecimals=0, step=1, min=0, max=3))
        self.setattr_argument("pmt_gating_edge",        EnumerationValue(["rising", "falling", "both"], default="rising"))
        self.pmt_switchon_time_mu = self.core.seconds_to_mu(560 * us)

    def prepare(self):
        """
        Set up the dataset and prepare things such that the kernel functions have minimal overhead.
        """
        # PMT devices
        self.pmt_counter = self.get_device("ttl_counter{:d}".format(self.pmt_input_channel))
        self.pmt_gating_edge = getattr(self.pmt_counter, 'gate_{:s}_mu'.format(self.pmt_gating_edge))
        self.ttl_signal = self.get_device("ttl{:d}".format(self.pmt_input_channel))
        self.ttl_power = self.get_device("ttl{:d}".format(self.pmt_power_channel))

        # timing
        self.time_bin_mu = self.core.seconds_to_mu(self.time_bin_us * us)
        self.time_reset_mu = self.core.seconds_to_mu(self.time_reset_us * us)

        # set up datasets
        self.set_dataset("pmt_dataset", zeros(self.repetitions), broadcast=True)

    @kernel
    def run(self):
        """
        Run the experimental sequence.
        """
        self.core.reset()

        # prepare devices
        self.prepareDevices()
        self.core.break_realtime()

        # program pulse sequence onto core DMA
        self.DMArecord()
        self.core.break_realtime()

        # retrieve pulse sequence handle
        handle = self.core_dma.get_handle(_DMA_HANDLE)
        self.core.break_realtime()

        # run the experiment
        for trial_num in range(self.repetitions):
            # run pulse sequence from core DMA
            self.core_dma.playback_handle(handle)

            # record pmt counts to dataset
            with parallel:
                self.mutate_dataset("pmt_dataset", trial_num, self.pmt_counter.fetch_count())
                delay_mu(self.time_reset_mu)

    @kernel
    def prepareDevices(self):
        """
        Prepare devices for the experiment.
        """
        # set signal TTL to correct direction for PMT
        self.core.break_realtime()
        self.ttl_signal.input()

        # turn PMT on and wait for turn-on time
        self.ttl_power.on()
        delay_mu(self.pmt_switchon_time_mu)

    @kernel
    def DMArecord(self):
        """
        Record onto core DMA the AOM sequence for a single data point.
        """
        with self.core_dma.record(_DMA_HANDLE):
            self.pmt_gating_edge(self.time_bin_mu)

    def analyze(self):
        """
        Analyze the results from the experiment.
        """
        pmt_counts = self.get_dataset("pmt_dataset")
        print("pmt counts:")
        print(pmt_counts)

        # todo: upload data to labrad
        # import labrad
        # cxn = labrad.connect()
        # print(cxn)
        # pass
