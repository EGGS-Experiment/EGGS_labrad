import numpy as np
from time import localtime, strftime
from labrad.units import WithUnit
from common.lib.servers.script_scanner.experiment import experiment
        
    
class scan_experiment_1D(experiment):
    '''
    Used to repeat an experiment multiple times
    '''
    def __init__(self, script_cls, parameter, minim, maxim, steps, units):
        self.script_cls = script_cls
        self.parameter = parameter
        self.units = units
        self.scan_points = np.linspace(minim, maxim, steps)
        self.scan_points = [WithUnit(pt, units) for pt in self.scan_points ]
        scan_name = self.name_format(script_cls.name)
        super(scan_experiment_1D,self).__init__(scan_name)
        
    def name_format(self, name):
        return 'Scanning {0} in {1}'.format(self.parameter, name)
    
    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
        self.navigate_data_vault(cxn, context)
    
    def run(self, cxn, context):
        for i, scan_value in enumerate(self.scan_points):
            if self.pause_or_stop(): return
            self.script.set_parameters({self.parameter: scan_value})
            self.script.set_progress_limits(100.0 * i / len(self.scan_points), 100.0 * (i + 1) / len(self.scan_points) )
            result = self.script.run(cxn, context)
            if self.script.should_stop: return
            if result is not None:
                cxn.data_vault.add([scan_value[self.units], result], context = context)
            self.update_progress(i)
    
    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S",local_time)
        directory = ['','ScriptScanner']
        directory.extend([strftime("%Y%b%d",local_time), strftime("%H%M_%S", local_time)])
        dv.cd(directory, True, context = context)
        dv.new(dataset_name, [('Iteration', 'Arb')], [(self.script.name, 'Arb', 'Arb')], context = context)
        dv.add_parameter('plotLive',True, context = context)
            
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan_points)
        self.sc.script_set_progress(self.ident,  progress)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)
