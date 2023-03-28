import labrad
from time import time, sleep
from datetime import datetime
from numpy import arange, linspace, zeros, mean, amax

from EGGS_labrad.servers.script_scanner.experiment import experiment

from EGGS_labrad.clients import createTrunk


class spectrum_analyzer_experiment(experiment):
    """
    Records data from spectrum analyzer.
    """

    name = 'Trace Recording'

    exp_parameters = []

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def initialize(self, cxn, context, ident):
        # properties
        self.ident = ident
        self.cxn = labrad.connect(name=self.name)

        #servers
        self.dv = self.cxn.data_vault
        self.sa = self.cxn.spectrum_analyzer_server
        self.cr = self.cxn.context()

        # set up spectrum analyzer
        self.sa.select_device(2)
        self.sa.attenuation(10)
        self.sa.frequency_span(10000)
        self.sa.bandwidth_resolution(100)
        self.sa.marker_toggle(1, True)

        # set up data vault
        self.set_up_datavault()

    def run(self, cxn, context, replacement_parameters={}):
        starttime = time()
        poll_delay_s = 10

        while True:
            sa_trace = self.sa.trace(1)
            elapsedtime = time() - starttime
            self.dv.add(elapsedtime, sa_trace, context=self.cr)

            sleep(poll_delay_s)

    def finalize(self, cxn, context):
        self.cxn.disconnect()

    def set_up_datavault(self):
        date = datetime.now()
        year = str(date.year)
        month = '{:02d}'.format(date.month)
        trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
        trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
        self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.cr)
        self.dv.new('Spectrum Analyzer', [('Elapsed time', 't')],
                          [ ('Signal Frequency',    'Frequency',    'Hz'),
            ('Signal Power',        'Power',        'dBm')], context=self.cr)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = spectrum_analyzer_experiment(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
