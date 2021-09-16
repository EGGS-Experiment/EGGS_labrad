from common.lib.servers.script_scanner.experiment import experiment
     
class single(experiment):
    '''
    runs a single epxeriment
    '''
    def __init__(self, script_cls):
        """
        script_cls: the experiment class
        """
        self.script_cls = script_cls
        super(single,self).__init__(self.script_cls.name)
    
    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
    
    def run(self, cxn, context, replacement_parameters = {}):
        self.script.run(cxn, context)
    
    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)

