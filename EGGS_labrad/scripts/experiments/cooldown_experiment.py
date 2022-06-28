import labrad
from time import time, sleep
from datetime import datetime

from EGGS_labrad.servers.script_scanner.experiment import experiment


class cooldown_experiment(experiment):
    """
    Records data when initiating cooldown of chamber.
    """

    name = 'Cooldown Recording'

    exp_parameters = []

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def initialize(self, cxn, context, ident):
        # properties
        self.ident = ident
        self.cxn = labrad.connect(name=self.name)

        # base servers
        self.dv = self.cxn.data_vault

        # device servers
        self.ls = self.cxn.lakeshore336_server
        #self.ni = self.cxn.niops03_server
        self.tt = self.cxn.twistorr74_server

        # dataset context
        self.c_ls = self.cxn.context()
        #self.c_ni = self.cxn.context()
        self.c_tt = self.cxn.context()

        # set up data vault
        self.set_up_datavault()

    def run(self, cxn, context, replacement_parameters={}):
        starttime = time()

        while True:
            sleep(2)
            temp_tmp = self.ls.read_temperature()
            #ip_tmp = self.ni.ip_pressure()
            press_tmp = self.tt.pressure()
            elapsedtime = time() - starttime
            self.dv.add(elapsedtime, temp_tmp[0], temp_tmp[1], temp_tmp[2], temp_tmp[3], context=self.c_ls)
            #self.dv.add([elapsedtime, ip_tmp], context=self.c_ni)
            self.dv.add([elapsedtime, press_tmp], context=self.c_tt)

    def finalize(self, cxn, context):
        self.cxn.disconnect()

    def set_up_datavault(self):
        date = datetime.now()
        year = str(date.year)
        month = '{:02d}'.format(date.month)
        trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
        trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
        self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_ls)
        self.dv.new('Lakeshore 336 Temperature Controller', [('Elapsed time', 't')],
                          [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'),
                           ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')], context=self.c_ls)

        #self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_ni)
        #self.dv.new('NIOPS03 Pump', [('Elapsed time', 's')], [('Ion Pump', 'Pressure', 'mbar')], context=self.c_ni)

        self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_tt)
        self.dv.new('Twistorr74 Turbopump', [('Elapsed time', 's')], [('Turbo Pump', 'Pressure', 'mbar')], context=self.c_tt)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.script_scanner
    exprt = cooldown_experiment(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
