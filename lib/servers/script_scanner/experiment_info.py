from treedict import TreeDict


class experiment_info(object):
    '''
    holds informaton about the experiment

    Attributes
    ----------
    name: str
    parameters: TreeDict
    required_parameters: list
    '''
    required_parameters = []
    name = ''

    def __init__(self, name=None, required_parameters=None):
        if name is not None:
            self.name = name
        if required_parameters is not None:
            self.required_parameters = required_parameters
        self.parameters = TreeDict()
