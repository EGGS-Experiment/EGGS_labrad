import numpy as np
from time import localtime, strftime
from labrad.units import WithUnit
from common.lib.servers.script_scanner.experiment import experiment
        
class scan_experiment_1D_measure(experiment):
    '''
    Used to repeat an experiment multiple times
    '''
    def __init__(self, scan_script_cls, measure_script_cls, parameter, minim, maxim, steps, units):
        self.scan_script_cls = scan_script_cls
        self.measure_script_cls = measure_script_cls
        self.parameter = parameter
        self.units = units
        self.scan_points = np.linspace(minim, maxim, steps)
        self.scan_points = [WithUnit(pt, units) for pt in self.scan_points ]
        scan_name = self.name_format(scan_script_cls.name, measure_script_cls.name)
        super(scan_experiment_1D_measure,self).__init__(scan_name)
        
    def name_format(self, scan_name, measure_name):
        return 'Scanning {0} in {1} while measuring {2}'.format(self.parameter, scan_name, measure_name)
    
    def initialize(self, cxn, context, ident):
        self.scan_script = self.make_experiment(self.scan_script_cls)
        self.measure_script = self.make_experiment(self.measure_script_cls)
        self.scan_script.initialize(cxn, context, ident)
        self.measure_script.initialize(cxn, context, ident)
        self.navigate_data_vault(cxn, context)
    
    def run(self, cxn, context):
        for i, scan_value in enumerate(self.scan_points):
            if self.pause_or_stop(): return
            self.scan_script.set_parameters({self.parameter: scan_value})
            self.scan_script.set_progress_limits(100.0 * i / len(self.scan_points), 100.0 * (i + 0.5) / len(self.scan_points) )
            self.scan_script.run(cxn, context)
            if self.scan_script.should_stop: return
            self.measure_script.set_progress_limits(100.0 * (i+0.5) / len(self.scan_points), 100.0 * (i + 1) / len(self.scan_points) )
            result = self.measure_script.run(cxn, context)
            if self.measure_script.should_stop: return
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
        dv.new(dataset_name, [('Iteration', 'Arb')], [(self.measure_script.name, 'Arb', 'Arb')], context = context)
        dv.add_parameter('plotLive',True, context = context)
            
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan_points)
        self.sc.script_set_progress(self.ident,  progress)
    
    def finalize(self, cxn, context):
        self.scan_script.finalize(cxn, context)
        self.measure_script.finalize(cxn, context)
