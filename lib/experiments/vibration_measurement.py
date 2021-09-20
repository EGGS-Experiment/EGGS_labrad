from common.lib.servers.script_scanner.scan_methods import experiment

import labrad
import numpy as np
import time
import datetime as datetime

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
        self.cxn = labrad.connect(name = 'Vibration Measurement')

        #base servers
        self.dv = self.cxn.data_vault
        self.p = self.parameters
        #self.grapher = self.cxn.real_simple_grapher

        #device servers
        #self.oscope = self.cxn.oscilloscope_server
        self.tempcontroller = self.cxn.lakeshore336server
        #self.pump = self.cxn.twistorr74server

        #set scannable parameters
        self.time_interval = self.p.VibrationMeasurement.dt

        #set up data vault
        self.c_result = self.cxn.context()
        self.set_up_datavault()

    def run(self, cxn, context, replacement_parameters={}):
        self.prevtime = time.time()

        while (time.time() - self.prevtime) <= self.time_interval:
            should_stop = self.pause_or_stop()
            if should_stop:
                break

            # pressure = self.pump.read_pressure()
            tempK = self.tempcontroller.read_temperature('0')
            # trace = self.oscope.get_trace('1')

            try:
                self.dv.add(time.time(), tempK, context = self.c_result)
            except:
                pass

            self.prevtime = time.time()

    def finalize(self, cxn, context):
        self.cxn.disconnect()

    def set_up_datavault(self):
        #set up folder
        date = datetime.datetime.now()
        year  = 'date.year'
        month = '%02d' % date.month  # Padded with a zero if one digit
        day   = '%02d' % date.day    # Padded with a zero if one digit
        trunk = year + '_' + month + '_' + day

        #create datasets
        self.dv.cd(['',year,month,trunk], True, context = self.c_result)
        dataset_temp = self.dv.new('Lakeshore 336 Temperature Controller',[('time', 't')], [('Temperature Diode 1', 'Temperature', 'K')], [('Temperature Diode 2', 'Temperature', 'K')], [('Temperature Diode 3', 'Temperature', 'K')], [('Temperature Diode 4', 'Temperature', 'K')], context = self.c_result)
        #dataset_pressure = self.dv.new('TwisTorr 74 Pressure Controller',[('time', 't')], [('Pump Pressure', 'Pressure', 'mTorr')], context = self.c_result)
        #dataset_oscope = self.dv.new('Rigol DS1104z Oscilloscope',[('time', 't')], [('Scope Trace', 'Scope Trace', '1')], context = self.c_result)

        #add parameters to data vault
        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter], context = self.c_result)

        #set live plotting
        #self.grapher.plot(dataset, 'bright/dark', False)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = vibration_measurement(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)