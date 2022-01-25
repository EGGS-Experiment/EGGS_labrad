import labrad
import numpy as np
import time
import datetime as datetime

from EGGS_labrad.servers.script_scanner.experiment import experiment

class vibration_measurement_ss(experiment):

    '''
    Records scope trace and its FFT, then converts them to csv
    '''

    name = 'Vibration Measurement SS'

    exp_parameters = []

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def initialize(self, cxn, context, ident):
        try:
            #properties
            self.ident = ident
            self.cxn = labrad.connect(name = self.name)

            #servers
            self.dv = self.cxn.data_vault
            self.grapher = self.cxn.grapher
            self.oscope = self.cxn.oscilloscope_server
            self.oscope.select_device()

            #dataset context
            self.c_oscope = self.cxn.context()

            #set up data vault
            self.set_up_datavault()

            #data: tmp
            self.dataDJ = None

        except Exception as e:
            print(e)

    def run(self, cxn, context, replacement_parameters={}):
        try:
            trace = self.oscope.get_trace(1)
            trace = np.array([trace[0], trace[1]]).transpose()
            self.dv.add_ex(trace, context = self.c_oscope)
            self.dataDJ = trace
        except Exception as e:
            print(e)
            raise

    def finalize(self, cxn, context):
        np.savetxt('data.csv', self.dataDJ, delimiter = ',')
        #todo: fft
        self.cxn.disconnect()

    def set_up_datavault(self):
        #set up folder
        date = datetime.datetime.now()
        year  = str(date.year)
        month = '%02d' % date.month     # Padded with a zero if one digit
        day   = '%02d' % date.day       # Padded with a zero if one digit
        hour  = '%02d' % date.hour      # Padded with a zero if one digit
        minute = '%02d' % date.minute   # Padded with a zero if one digit

        trunk1 = year + '_' + month + '_' + day
        trunk2 = self.name + '_' + hour + ':' + minute

        self.filename = trunk2

        #create datasets
            #oscope
        self.dv.cd(['','Experiments', year, month, trunk1, trunk2], True, context=self.c_oscope)
        dataset_oscope = self.dv.new('Oscilloscope Trace',[('Time', 's')], [('Scope Trace', 'Scope Trace', '1')], context = self.c_oscope)

        #set live plotting
        #self.grapher.plot(dataset_oscope, 'bright/dark', False)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = vibration_measurement_ss(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)