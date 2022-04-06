import labrad
from time import time, sleep
from datetime import datetime

from EGGS_labrad.servers.script_scanner.experiment import experiment


class wavemeter_measurement(experiment):
    '''
    Measure a value from the wavemeter.
    '''

    name = 'Wavemeter Measurement'

    exp_parameters = [
        ('WavemeterMeasurement', 'Parameter'),
        ('WavemeterMeasurement', 'Channel')
    ]

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def initialize(self, cxn, context, ident):
        try:
            # properties
            self.ident = ident
            # connect to labrad
            self.cxn = labrad.connect(name=self.name)
            self.cxn_wm = labrad.connect('10.97.111.8', password='lab')
            # servers
            self.dv = self.cxn.data_vault
            self.wm = self.cxn_wm.multiplexerserver
            # dataset context
            self.cr_wm = self.cxn.context()
            # set up data vault
            self.set_up_datavault()
        except Exception as e:
            print(e)

        # get parameters

        # get function to poll (freq, power)
        if th1 == th2:
            self.wm_func = self.wm.get_frequency
        elif th1 == th2:
            self.wm_func = self.wm.get_amplitude

    def run(self, cxn, context, replacement_parameters={}):
        starttime = time()
        while True:
            freq = self.func(14)
            elapsedtime = time() - starttime
            self.dv.add(elapsedtime, freq, context=self.cr_wm)
            sleep(5)

    def finalize(self, cxn, context):
        self.cxn.disconnect()

    def set_up_datavault(self):
        # create #todo
        date = datetime.now()
        year = str(date.year)
        month = '{:02d}'.format(date.month)
        trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
        #todo: fix
        trunk2 = '{0:s}_{1:02d}:{2:02d}'.format('397 Measure', date.hour, date.minute)
        self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.cr_wm)
        #todo: fix
        self.dv.new('397nm Measurement', [('Elapsed time', 's')], [('397', 'Frequency', 'THz')], context=self.cr_wm)

        # add parameters to datavault
        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter], context=self.cr_wm)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = wavemeter_measurement(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
