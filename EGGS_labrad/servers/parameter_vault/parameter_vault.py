"""
### BEGIN NODE INFO
[info]
name = Parameter Vault
version = 2.1.1
description = Loads experiment parameters from data vault
instancename = Parameter Vault

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from twisted.internet.defer import inlineCallbacks
from labrad.server import LabradServer, setting, Signal


class ParameterVault(LabradServer):
    """
    Uses the registry to store ongoing experimental parameters.
    """
    
    name = "Parameter Vault"

    # this sets the directory for parameter vault to use
    registryDirectory = ['', 'Servers', 'Parameter Vault']


    # SIGNALS
    onParameterChange = Signal(612512, 'signal: parameter change', '(ss)')


    # SETUP
    @inlineCallbacks
    def initServer(self):
        self.listeners = set()
        self.parameters = {}
        yield self._load_parameters()
        
    @inlineCallbacks
    def stopServer(self):
        try:
            yield self._save_parameters()
        except AttributeError:
            # if values don't exist yet, i.e stopServer called due to an Identification Error
            pass

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified


    # SETTINGS
    @setting(0, "Set Parameter", collection='s', parameter_name='s', value='?', full_info='b', returns='')
    def setParameter(self, c, collection, parameter_name, value, full_info=False):
        """
        Sets the value of a parameter.
        Arguments:
            collection (str)        : the collection of parameters to use.
            parameter_name (str)    : the name of the parameter.
            value                   : the value to set the parameter to.
            full_info (bool)        : whether the parameter value contains
        """
        # todo: use the idea of parameter items
        key = (collection, parameter_name)
        if key not in self.parameters.keys():
            raise Exception("Parameter Not Found: {}".format(key))
        if full_info:
            self.parameters[key] = value
        else:
            self.parameters[key] = self._save_full(key, value)
        notified = self.getOtherListeners(c)
        self.onParameterChange((key[0], key[1]), notified)

    @setting(1, "Get Parameter", collection='s', parameter_name='s', checked='b', returns=['?'])
    def getParameter(self, c, collection, parameter_name, checked=True):
        """
        Get the value of a parameter.
        Arguments:
            collection      (str)   : the name of the parameter collection to get from.
            parameter_name  (str)   : the name of the parameter to get.
            checked         (bool)  : whether to check that a parameter meets the rules for its parameter type.
        Returns:
            the parameter value
        """
        # todo: use the idea of parameter items
        # try to get the parameter value
        key = (collection, parameter_name)
        try:
            value = self.parameters[key]
        except KeyError:
            raise Exception("Parameter Not Found: {}".format(key))

        # check that the value meets the rules for its parameter type
        if checked:
            value = self._check_parameter(key, value)
        return value

    @setting(2, "Get Collections", returns='*s')
    def get_collection_names(self, c):
        """
        Returns all collections of parameters stored in the parameter vault.
        Returns:
            list(str): a list of all currently stored parameter collections.
        """
        collections = set([key[0] for key in self.parameters.keys()])
        return list(collections)

    @setting(3, "Get Parameter Names", collection='s', returns='*s')
    def getParameterNames(self, c, collection):
        """
        Returns the names of all stored parameters within a collection.
        Arguments:
            collection (str): the collection to get parameter names from.
        Returns:
            list(str): a list of all currently stored parameter names.
        """
        return [key[1] for key, item in self.parameters.items() if key[0] == collection]

    @setting(4, "Refresh Parameters", returns='')
    def refresh_parameters(self, c):
        """
        Saves all parameters to the registry, then reloads them.
        """
        yield self._save_parameters()
        yield self._load_parameters()

    @setting(5, "Reload Parameters", returns='')
    def reload_parameters(self, c):
        """
        Discards current parameters and reloads them from registry.
        """
        yield self._load_parameters()

    @setting(6, "Save Parameters To Registry", returns='')
    def saveParametersToRegistry(self, c):
        """
        Saves all currently stored parameters to the registry.
        """
        yield self._save_parameters()
        
    
    # HELPERS
    @inlineCallbacks
    def _load_parameters(self):
        """
        Recursively adds all parameters to the holding dictionary self.parameters.
        """
        yield self._addParametersInDirectory(self.registryDirectory, [])

    @inlineCallbacks
    def _addParametersInDirectory(self, topPath, subPath):
        """
        A recursive function that gets any parameters in the given directory.
        Arguments:
            topPath (list(str)): the top-level directory that Parameter vault has access to.
                                    this isn't modified by any recursive calls.
            subPath (list(str)): the subdirectory from which to get parameters.
        """
        # get everything in the given directory
        yield self.client.registry.cd(topPath + subPath)
        directories, parameters = yield self.client.registry.dir()

        # only add parameters in subdirectories
        # and ignore those in the top-level directory
        if subPath:
            for parameter in parameters:
                key = tuple(subPath + [parameter])
                value = yield self.client.registry.get(parameter)
                self.parameters[key] = value

        # recursive step: get parameters in any subfolders
        for directory in directories:
            newpath = subPath + [directory]
            yield self._addParametersInDirectory(topPath, newpath)

    @inlineCallbacks
    def _save_parameters(self):
        """
        Save the latest parameters into registry.
        """
        regDir = self.registryDirectory
        for key, value in self.parameters.items():
            key = list(key)
            parameter_name = key.pop()
            fullDir = regDir + key
            yield self.client.registry.cd(fullDir)
            yield self.client.registry.set(parameter_name, value)

    def _save_full(self, key, value):
        """
        Checks that the new parameter item is valid.
        Returns:
            tuple(str, parameter_item): the new parameter value.
        """
        # todo: use the idea of parameter items
        param_type, item = self.parameters[key]
        if param_type == 'parameter':
            # check that the parameter is within the given range
            assert item[0] <= value <= item[1], "Parameter Out of Bounds: {}".format(key[1])
            # replace the old parameter with the new value
            item[2] = value
            return (param_type, item)
        else:
            raise Exception("Parameter not a checkable type.")

    def _check_parameter(self, key, value):
        """
        Check that parameter items meet the rules for the parameter type.
        Arguments:
            key (str): the name of the parameter.
            value (tuple(str, item)): a tuple of parameter type and the parameter item.
                                        depending on the parameter type, the parameter item
                                        can be of different lengths.
        Returns:
            the parameter item
        """
        # todo: use the idea of parameter items
        param_type, item = value

        # error strings
        parameter_bound = "Parameter Out of Bounds: {}"
        bad_selection = "Incorrect selection made in {}"

        if (param_type == 'parameter') or (param_type == 'duration_bandwidth'):
            assert item[0] <= item[2] <= item[1], parameter_bound.format(key)
            return item[2]
        elif param_type == 'scan':
            minim, maxim = item[0]
            start, stop, steps = item[1]
            assert minim <= start <= maxim, parameter_bound.format(key)
            assert minim <= stop <= maxim, parameter_bound.format(key)
            return (start, stop, steps)
        elif param_type == 'selection_simple':
            assert item[0] in item[1], bad_selection.format(key)
            return item[0]
        elif param_type == 'line_selection':
            assert item[0] in dict(item[1]).keys(), bad_selection.format(key)
            return item[0]
        # return the entire item
        elif param_type in ('string', 'bool', 'sideband_selection', 'spectrum_sensitivity'):
            return item
        # otherwise just return the value
        else:
            return value


if __name__ == "__main__":
    from labrad import util
    util.runServer(ParameterVault())
