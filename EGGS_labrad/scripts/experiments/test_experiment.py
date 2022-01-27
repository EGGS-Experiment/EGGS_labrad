import labrad
import numpy as np
import time
import datetime as datetime

from EGGS_labrad.servers.script_scanner.experiment import experiment


class test_experiment(experiment):
    '''
    Tests base experiment functionality
    '''

    name = 'Test'

    exp_parameters = [
                    ('Test', 'param1'),
                    ('Test', 'param2')
                    ]

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def initialize(self, cxn, context, ident):
        #properties
        self.ident = ident
        self.cxn = labrad.connect(name = self.name)

        #base servers
        self.dv = self.cxn.data_vault
        self.p = self.parameters
        #self.grapher = self.cxn.real_simple_grapher

        #device servers
        #self.tempcontroller = self.cxn.lakeshore336server

        #set scannable parameters
        self.param1 = self.p.Test.param1
        self.param1 = 2.0

        self.param2 = self.p.Test.param2
        self.param2 = 10.0

        #convert parameter to labrad type
        #welp, todo

        #dataset context
        self.c_data1 = self.cxn.context()
        self.c_data2 = self.cxn.context()

        #set up data vault
        self.set_up_datavault()

    def run(self, cxn, context, replacement_parameters={}):
        prevtime = time.time()
        starttime = time.time()
        data2 = (np.arange(0, 1000), np.random.rand(1000))
        data2 = np.array([data2[0], data2[1]]).transpose()
        self.dv.add_ex(data2, context=self.c_data2)

        while True:
            if self.pause_or_stop() == True:
                break
            elif (time.time() - prevtime) <= 1:
                continue
            data1 = np.array([1, 2, 3, 4])
            elapsedtime = time.time() - starttime
            prevtime = time.time()
            try:
                self.dv.add(elapsedtime, data1[0], data1[1], data1[2], data1[3], context=self.c_data1)
            except Exception as e:
                print(e)

    def finalize(self, cxn, context):
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

        #create datasets
            #data 1
        self.dv.cd(['', 'Experiments', year, month, trunk1, trunk2], True, context = self.c_data1)
        dataset_1 = self.dv.new('Test Data 1',[('Elapsed time', 't')], [('Trend 1', 'Value', 'arb'), ('Trend 2', 'Value', 'arb'), \
                                                                                             ('Trend 3', 'Value', 'arb'), ('Trend 4', 'Value', 'arb')] , context = self.c_data1)
            #data 2
        self.dv.cd(['','Experiments', year, month, trunk1, trunk2], True, context=self.c_data2)
        dataset_2 = self.dv.new('Test Data 2',[('Elapsed time', 't')], [('Trend 2.1', 'Value 2', 'arb')], context = self.c_data2)

        #add parameters to data vault
        # for parameter in self.p:
        #     self.dv.add_parameter(parameter, self.p[parameter], context = self.c_data1)
        #     self.dv.add_parameter(parameter, self.p[parameter], context=self.c_data2)

        #set live plotting
        #self.grapher.plot(dataset, 'bright/dark', False)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = test_experiment(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)