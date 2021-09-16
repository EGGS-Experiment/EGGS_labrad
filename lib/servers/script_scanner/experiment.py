import traceback
import labrad
from treedict import TreeDict
from common.lib.servers.script_scanner.experiment_info import experiment_info


class experiment(experiment_info):

    def __init__(self, name=None, required_parameters=None, cxn=None,
                 min_progress=0.0, max_progress=100.0,):
        required_parameters = self.all_required_parameters()
        super(experiment, self).__init__(name, required_parameters)
        self.cxn = cxn
        self.pv = None
        self.sc = None
        self.context = None
        self.min_progress = min_progress
        self.max_progress = max_progress
        self.should_stop = False

    def _connect(self):
        if self.cxn is None:
            try:
                self.cxn = labrad.connect()
            except Exception as error:
                error_message = error + '\n' + "Not able to connect to LabRAD"
                raise Exception(error_message)
        try:
            self.sc = self.cxn.servers['ScriptScanner']
        except KeyError as error:
            error_message = error + '\n' + "ScriptScanner is not running"
            raise KeyError(error_message)
        try:
            self.pv = self.cxn.servers['ParameterVault']
        except KeyError as error:
            error_message = error + '\n' + "ParameterVault is not running"
            raise KeyError(error_message)
        try:
            self.context = self.cxn.context()
        except Exception as error:
            error_message = error + '\n' + "self.cxn.context is not available"
            raise Exception(error_message)

    def execute(self, ident):
        '''
        executes the experiment
        '''
        self.ident = ident
        try:
            self._connect()
            self._initialize(self.cxn, self.context, ident)
            self._run(self.cxn, self.context)
            self._finalize(self.cxn, self.context)
        except Exception as e:
            reason = traceback.format_exc()
            print reason
            if hasattr(self, 'sc'):
                self.sc.error_finish_confirmed(self.ident, reason)
        finally:
            if hasattr(self, 'cxn'):
                if self.cxn is not None:
                    self.cxn.disconnect()
                    self.cxn = None

    def _initialize(self, cxn, context, ident):
        self._load_required_parameters()
        self.initialize(cxn, context, ident)
        self.sc.launch_confirmed(ident)

    def _run(self, cxn, context):
        self.run(cxn, context)

    def _load_required_parameters(self, overwrite=False):
        d = self._load_parameters_dict(self.required_parameters)
        self.parameters.update(d, overwrite=overwrite)

    def _load_parameters_dict(self, params):
        '''loads the required parameter into a treedict'''
        d = TreeDict()
        for collection, parameter_name in params:
            try:
                value = self.pv.get_parameter(collection, parameter_name)
            except Exception as e:
                print e
                message = "In {}: Parameter {} not found among Parameter Vault parameters"
                raise Exception (message.format(self.name, (collection, parameter_name)))
            else:
                d['{0}.{1}'.format(collection, parameter_name)] = value
        return d

    def set_parameters(self, parameter_dict):
        '''
        can reload all parameter values from parameter_vault or replace
        parameters with values from the provided parameter_dict
        '''
        if isinstance(parameter_dict, dict):
            udpate_dict = TreeDict()
            for (collection,parameter_name), value in parameter_dict.iteritems():
                udpate_dict['{0}.{1}'.format(collection, parameter_name)] = value
        elif isinstance(parameter_dict, TreeDict):
            udpate_dict = parameter_dict
        else:
            message = "Incorrect input type for the replacement dictionary"
            raise Exception(message)
        self.parameters.update(udpate_dict)

    def reload_some_parameters(self, params):
        d = self._load_parameters_dict(params)
        self.parameters.update(d)

    def reload_all_parameters(self):
        self._load_required_parameters(overwrite=True)

    def _finalize(self, cxn, context):
        self.finalize(cxn, context)
        self.sc.finish_confirmed(self.ident)

    # useful functions to be used in subclasses
    @classmethod
    def all_required_parameters(cls):
        return []

    def pause_or_stop(self):
        '''
        allows to pause and to stop the experiment
        '''
        self.should_stop = self.sc.pause_or_stop(self.ident)
        if self.should_stop:
            self.sc.stop_confirmed(self.ident)
        return self.should_stop

    def make_experiment(self, subexprt_cls):
        subexprt = subexprt_cls(cxn=self.cxn)
        subexprt._connect()
        subexprt._load_required_parameters()
        return subexprt

    def set_progress_limits(self, min_progress, max_progress):
        self.min_progress = min_progress
        self.max_progress = max_progress

    # functions to reimplement in the subclass
    def initialize(self, cxn, context, ident):
        '''
        implemented by the subclass
        '''

    def run(self, cxn, context, replacement_parameters={}):
        '''
        implemented by the subclass
        '''

    def finalize(self, cxn, context):
        '''
        implemented by the subclass
        '''
