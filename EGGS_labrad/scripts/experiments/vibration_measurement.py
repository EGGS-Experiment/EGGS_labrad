import labrad
import numpy as np
import time
import datetime as datetime

from EGGS_labrad.servers.script_scanner.experiment import experiment

class vibration_measurement(experiment):

    '''
    Records scope trace and its FFT, pressure, and temperature
    '''

    name = 'Vibration Measurement'

    exp_parameters = [
                    ('VibrationMeasurement', 'dt'),
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
        self.oscope = self.cxn.oscilloscope_server
        self.oscope.select_device()
        self.tempcontroller = self.cxn.lakeshore336server
        self.pump = self.cxn.twistorr74server

        #set scannable parameters
        self.time_interval = self.p.VibrationMeasurement.dt
        self.time_interval = 2.0

        #convert parameter to labrad type
        #welp, todo

        #dataset context
        self.c_temp = self.cxn.context()
        self.c_press = self.cxn.context()
        self.c_oscope = self.cxn.context()

        #set up data vault
        self.set_up_datavault()

    def run(self, cxn, context, replacement_parameters={}):
        starttime = time.time()

        while (True):
            if (self.pause_or_stop() == True):
                break

            #only take data at certain time intervals
            elapsedtime = time.time() - starttime
            if (elapsedtime) <= self.time_interval:
                continue

            #get data
            pressure = self.pump.pressure()
            tempK = self.tempcontroller.read_temperature('0')
            trace = self.oscope.get_trace(1)
            trace = np.array([trace[0], trace[1]]).transpose()

            try:
                self.dv.add(elapsedtime, tempK[0], tempK[1], tempK[2], tempK[3], context = self.c_temp)
                self.dv.add(elapsedtime, pressure, context=self.c_press)
                self.dv.add_ex(trace, context = self.c_oscope)
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
            #temp controller
        self.dv.cd(['', 'Experiments', year, month, trunk1, trunk2], True, context = self.c_temp)
        dataset_temp = self.dv.new('Lakeshore 336 Temperature Controller',[('Elapsed time', 't')], [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'), \
                                                                                             ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')] , context = self.c_temp)
            #pressure
        self.dv.cd(['', 'Experiments', year, month, trunk1, trunk2], True, context=self.c_press)
        dataset_pressure = self.dv.new('TwisTorr 74 Pressure Controller',[('Elapsed time', 't')], [('Pump Pressure', 'Pressure', 'mTorr')], context = self.c_press)
            #oscope
        self.dv.cd(['','Experiments', year, month, trunk1, trunk2], True, context=self.c_oscope)
        dataset_oscope = self.dv.new('Rigol DS1104z Oscilloscope',[('Elapsed time', 't')], [('Scope Trace', 'Voltage', 'V')], context = self.c_oscope)

        #add parameters to data vault
        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter], context = self.c_temp)
            self.dv.add_parameter(parameter, self.p[parameter], context = self.c_press)

        #set live plotting
        #self.grapher.plot(dataset, 'bright/dark', False)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = vibration_measurement(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)