import labrad
from time import time, sleep
from datetime import datetime

from EGGS_labrad.servers.script_scanner.experiment import experiment


class rga_measurement(experiment):
    '''
    Measure a value from the RGA.
    '''

    name = 'RGA Measurement'

    exp_parameters = [
        ('RGAMeasurement', 'channel')
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
            # servers
            self.dv = self.cxn.data_vault
            # dataset context
            self.cr_wm = self.cxn.context()
            # assign parameters
            self.p = self.parameters
            self.chan = self.p.WavemeterMeasurement.channel
            # get channel name and wavelength
            # get function to poll (freq, power)
            lock_freq = float(self.wm.get_pid_course(self.chan))
            self.lock_wav = round(3e8 / lock_freq / 1e3)
            # set up data vault
            self.set_up_datavault()
            # elif th1 == th2:
            #     self.wm_func = self.wm.get_amplitude
        except Exception as e:
            print(e)

    def run(self, cxn, context, replacement_parameters={}):
        starttime = time()
        while (True) and (not self.pause_or_stop()):
            freq = self.wm_func(self.chan)
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
        trunk2 = '{0:d} Measure_{1:02d}:{2:02d}'.format(self.lock_wav, date.hour, date.minute)
        self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.cr_wm)
        self.dv.new('{:d}nm Measurement'.format(self.lock_wav), [('Elapsed time', 's')],
                    [('{:d}'.format(self.lock_wav), 'Frequency', 'THz')], context=self.cr_wm)

        # add parameters to datavault
        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter], context=self.cr_wm)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = rga_measurement(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
