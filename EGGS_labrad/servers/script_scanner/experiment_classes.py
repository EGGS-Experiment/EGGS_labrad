"""
Superclass of experiments.
"""
import numpy as np
from labrad.units import WithUnit
from experiment import experiment
from time import localtime, strftime

__all__ = ["single", "scan_experiment_1D", "scan_experiment_1D_measure", "repeat_reload"]


"""
Individual Experiments
"""


class single(experiment):
    '''
    Runs a single experiment.
    '''

    def __init__(self, script_cls):
        """
        script_cls: the experiment class
        """
        self.script_cls = script_cls
        super(single, self).__init__(self.script_cls.name)

    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)

    def run(self, cxn, context, replacement_parameters={}):
        self.script.run(cxn, context)

    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)


"""
Scanning Experiments
"""


class scan_experiment_1D(experiment):
    '''
    Used to repeat an experiment multiple times.
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


class scan_experiment_1D_measure(experiment):
    '''
    Used to repeat an experiment multiple times.
    Same as scan_experiment_1D but with a measure script as well.
    '''

    def __init__(self, scan_script_cls, measure_script_cls, parameter, minim, maxim, steps, units):
        self.scan_script_cls = scan_script_cls
        self.measure_script_cls = measure_script_cls
        self.parameter = parameter
        self.units = units
        self.scan_points = np.linspace(minim, maxim, steps)
        self.scan_points = [WithUnit(pt, units) for pt in self.scan_points]
        scan_name = self.name_format(scan_script_cls.name, measure_script_cls.name)
        super(scan_experiment_1D_measure, self).__init__(scan_name)

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
            self.scan_script.set_progress_limits(100.0 * i / len(self.scan_points),
                                                 100.0 * (i + 0.5) / len(self.scan_points))
            self.scan_script.run(cxn, context)
            if self.scan_script.should_stop: return
            self.measure_script.set_progress_limits(100.0 * (i + 0.5) / len(self.scan_points),
                                                    100.0 * (i + 1) / len(self.scan_points))
            result = self.measure_script.run(cxn, context)
            if self.measure_script.should_stop: return
            if result is not None:
                cxn.data_vault.add([scan_value[self.units], result], context=context)
            self.update_progress(i)

    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S", local_time)
        directory = ['', 'ScriptScanner']
        directory.extend([strftime("%Y%b%d", local_time), strftime("%H%M_%S", local_time)])
        dv.cd(directory, True, context=context)
        dv.new(dataset_name, [('Iteration', 'Arb')], [(self.measure_script.name, 'Arb', 'Arb')], context=context)
        dv.add_parameter('plotLive', True, context=context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(
            self.scan_points)
        self.sc.script_set_progress(self.ident, progress)

    def finalize(self, cxn, context):
        self.scan_script.finalize(cxn, context)
        self.measure_script.finalize(cxn, context)


class repeat_reload(experiment):
    '''
    Used to repeat an experiment multiple times, while reloading the parameters every repeatition
    '''
    def __init__(self, script_cls, repetitions, save_data=False):
        self.script_cls = script_cls
        self.repetitions = repetitions
        self.save_data = save_data
        scan_name = self.name_format(script_cls.name)
        super(repeat_reload, self).__init__(scan_name)

    def name_format(self, name):
        return 'Repeat {0} {1} times'.format(name, self.repetitions)

    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
        if self.save_data:
            self.navigate_data_vault(cxn, context)

    def run(self, cxn, context):
        for i in range(self.repetitions):
            if self.pause_or_stop(): return
            self.script.reload_all_parameters()
            self.script.set_progress_limits(100.0 * i / self.repetitions, 100.0 * (i + 1) / self.repetitions)
            result = self.script.run(cxn, context)
            if self.script.should_stop: return
            if self.save_data and result is not None:
                cxn.data_vault.add([i, result], context=context)
            self.update_progress(i)

    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S", local_time)
        directory = ['', 'ScriptScanner']
        directory.extend([strftime("%Y%b%d", local_time), strftime("%H%M_%S", local_time)])
        dv.cd(directory, True, context=context)
        dv.new(dataset_name, [('Iteration', 'Arb')], [(self.script.name, 'Arb', 'Arb')], context=context)
        dv.add_parameter('plotLive', True, context=context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(
            iteration + 1.0) / self.repetitions
        self.sc.script_set_progress(self.ident, progress)

    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)
