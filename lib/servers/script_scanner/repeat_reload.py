from time import localtime, strftime

from common.lib.servers.script_scanner.experiment import experiment

class repeat_reload(experiment):
    '''
    Used to repeat an experiment multiple times, while reloading the parameters every repeatition
    '''
    def __init__(self, script_cls, repetitions, save_data = False):
        self.script_cls = script_cls
        self.repetitions = repetitions
        self.save_data = save_data
        scan_name = self.name_format(script_cls.name)
        super(repeat_reload,self).__init__(scan_name)

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
            self.script.set_progress_limits(100.0 * i / self.repetitions, 100.0 * (i + 1) / self.repetitions )
            result = self.script.run(cxn, context)
            if self.script.should_stop: return
            if self.save_data and result is not None:
                cxn.data_vault.add([i, result], context = context)
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
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / self.repetitions
        self.sc.script_set_progress(self.ident,  progress)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)
