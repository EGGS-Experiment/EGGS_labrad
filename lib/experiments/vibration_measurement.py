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

        #dataset context
        self.c_temp_1 = self.cxn.context()
        self.c_temp_2 = self.cxn.context()
        self.c_temp_3 = self.cxn.context()
        self.c_temp_4 = self.cxn.context()

        #set up data vault
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

            # crt_time = datetime.datetime.now()
            # hournow = str(crt_time.hour)
            # minnow = str(crt_time.minute)
            # secnow = str(crt_time.second)
            # formatted_time = hournow + ":" + minnow + ":" + secnow
            #print(tempK)
            try:
                self.dv.add(time.time(), tempK[0], context = self.c_temp_1)
                self.dv.add(time.time(), tempK[1], context = self.c_temp_2)
                self.dv.add(time.time(), tempK[2], context = self.c_temp_3)
                self.dv.add(time.time(), tempK[3], context = self.c_temp_4)
            except:
                pass

            self.prevtime = time.time()

    def finalize(self, cxn, context):
        self.cxn.disconnect()

    def set_up_datavault(self):
        #set up folder
        date = datetime.datetime.now()
        year  = str(date.year)
        month = '%02d' % date.month  # Padded with a zero if one digit
        day   = '%02d' % date.day    # Padded with a zero if one digit
        trunk = year + '_' + month + '_' + day

        #create datasets
        self.dv.cd(['',year,month,trunk], True, context = self.c_temp_1)
        dataset_temp1 = self.dv.new('Lakeshore 336 Temperature Controller',[('time', 't')], [('Temperature Diode 1', 'Temperature', 'K')], context = self.c_temp_1)
        self.dv.cd(['', year, month, trunk], True, context=self.c_temp_2)
        dataset_temp2 = self.dv.new('Lakeshore 336 Temperature Controller',[('time', 't')], [('Temperature Diode 2', 'Temperature', 'K')], context = self.c_temp_2)
        self.dv.cd(['', year, month, trunk], True, context=self.c_temp_3)
        dataset_temp = self.dv.new('Lakeshore 336 Temperature Controller', [('time', 't')], [('Temperature Diode 4', 'Temperature', 'K')], context = self.c_temp_3)
        self.dv.cd(['', year, month, trunk], True, context=self.c_temp_4)
        dataset_temp = self.dv.new('Lakeshore 336 Temperature Controller', [('time', 't')], [('Temperature Diode 4', 'Temperature', 'K')], context = self.c_temp_4)
        #dataset_pressure = self.dv.new('TwisTorr 74 Pressure Controller',[('time', 't')], [('Pump Pressure', 'Pressure', 'mTorr')], context = self.c_result)
        #dataset_oscope = self.dv.new('Rigol DS1104z Oscilloscope',[('time', 't')], [('Scope Trace', 'Scope Trace', '1')], context = self.c_result)

        #add parameters to data vault
        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter], context = self.c_temp_1)
            self.dv.add_parameter(parameter, self.p[parameter], context=self.c_temp_2)
            self.dv.add_parameter(parameter, self.p[parameter], context=self.c_temp_3)
            self.dv.add_parameter(parameter, self.p[parameter], context=self.c_temp_4)

        #set live plotting
        #self.grapher.plot(dataset, 'bright/dark', False)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = vibration_measurement(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)