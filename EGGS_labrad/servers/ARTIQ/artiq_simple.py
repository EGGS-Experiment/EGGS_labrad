"""
### BEGIN NODE INFO
[info]
name = ARTIQ Server Simple
version = 1.0
description = Pulser using the ARTIQ box. Backwards compatible with old pulse sequences and experiments.
instancename = ARTIQ Server Simple

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
# labrad imports
from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks
# artiq imports
from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager
from EGGS_labrad.config import device_db as device_db_module


class ARTIQ_api_Simple(object):
    """
    A simple API for the ARTIQ box, with only the DAC (zotino) functions.
    Directly accesses the hardware on the box without having to use artiq_master.
    """

    # STARTUP
    def __init__(self, ddb_filepath):
        # Create a DeviceDB object (device database) from
        # the device_db.py file at the specified filepath.
        # The ddb_filepath should be passed by the ARTIQ server.
        devices = DeviceDB(ddb_filepath)
        # We set the device_db structure (i.e. the contents of the
        # device_db.py file) as an instance variable.
        self.device_db = devices.get_device_db()
        # Create a DeviceManager object using the DeviceDB object.
        # This is necessary since the DeviceDB object, in addition
        # to containing the contents of the device_db.py file, has
        # functions used by the DeviceManager class to interact with
        # the device_db structure.
        self.device_manager = DeviceManager(devices)
        self._getDevices()
        self.initializeDAC()

    def _getDevices(self):
        """
        Gets ARTIQ device objects.
        Devices can be set and used similar to how they
        would normally be in a regular ARTIQ experiment.
        """
        # Get core devices.
        self.core = self.device_manager.get("core")
        self.core_dma = self.device_manager.get("core_dma")
        # Store devices in dictionary where device
        # name is key and device itself is value.
        self.ttlout_list = {}
        # Store DAC type.
        self.zotino = None
        self.fastino = None
        self.dacType = None

        # assign names and devices
        for name, params in self.device_db.items():
            # only get devices with named class
            if 'class' not in params:
                continue
            # set device as attribute
            devicetype = params['class']
            device = self.device_manager.get(name)
            # add the output TTL classes to a dictionary
            # forconvenience.
            if devicetype == 'TTLOut':
                self.ttlout_list[name] = device
            # Need to specify both device types since
            # all kernel functions need to be valid.
            # See the docstring before the DAC section
            # for more information.
            elif devicetype == 'Zotino':
                self.zotino = device
                self.fastino = device
                self.dacType = devicetype
            elif devicetype == 'Fastino':
                self.fastino = device
                self.zotino = device
                self.dacType = devicetype

    # TTL
    def setTTL(self, ttlname, state):
        """
        Manually set the state of a TTL.
        The difference between setTTL and _setTTL is that setTTL
        is not a kernel function (i.e. it takes place on the computer
        rather than on the ARTIQ box), while _setTTL is a kernel function
        (i.e. it takes place on the ARTIQ box).
        This is because we choose to hold the TTL device classes in a dictionary,
        and ARTIQ doesn't let us use dictionary objects in kernel functions.
        """
        try:
            # get device object from the dictionary holding
            # all the output TTL classes
            dev = self.ttlout_list[ttlname]
        except KeyError:
            raise Exception('Invalid device name.')
        # call the kernel function which sets the TTL
        self._setTTL(dev, state)

    @kernel
    def _setTTL(self, dev, state):
        self.core.reset()
        if state:
            dev.on()
        else:
            dev.off()

    # DAC/ZOTINO

    '''
    Notice that all the DAC functions are kernel functions and are called
    directly by the ARTIQ server. This is because there is only one DAC,
    so we don't need to use any dictionaries to store the DAC object classes.
    
    Also, notice that there are two sets of functions: one for the Zotino, and
    one for the Fastino. This is because objects inside kernel functions cannot
    be None. This is why, in _getDevices(), we had to explicitly set the Zotino
    and Fastino instance variables to whatever DAC we have, since otherwise
    either object could be None, which is not allowed.
    '''

    @kernel
    def initializeDAC(self):
        """
        Initialize the DAC.
        """
        self.core.reset()
        self.zotino.init()

    @kernel
    def setZotino(self, channel_num, volt_mu):
        """
        Set the voltage of a DAC register.
        """
        self.core.reset()
        self.zotino.write_dac_mu(channel_num, volt_mu)
        self.zotino.load()

    @kernel
    def setZotinoGain(self, channel_num, gain_mu):
        """
        Set the gain of a DAC channel.
        """
        self.core.reset()
        self.zotino.write_gain_mu(channel_num, gain_mu)
        self.zotino.load()


class ARTIQ_Server_Simple(LabradServer):
    """
    A simple version of the main ARTIQ server
    just to help understand how the ARTIQ server works.
    """

    name = 'ARTIQ Server Simple'
    regKey = 'ARTIQ Server Simple'

    # STARTUP
    @inlineCallbacks
    def initServer(self):
        # Initialize the ARTIQ api and set it as an instance
        # variable so we can use it later on.
        ddb_filepath = device_db_module.__file__
        self.api = ARTIQ_api_Simple(ddb_filepath)
        # This tries to create connections to the ARTIQ Master
        # to use its experiment scheduler and dataset manager.
        # Error handling in _setClients handles the case where we
        # cannot connect to ARTIQ Master (e.g. it doesn't exist)
        # and allows us to start up anyways, just without scheduler
        # and dataset functionality.
        yield self._setClients()
        # This is just used to import variables and conversion
        # functions from the ARTIQ package.
        yield self._setVariables()
        # This basically just takes the list of devices from our API.
        yield self._setDevices()

    def _setClients(self):
        """
        Create clients to ARTIQ master.
        Used to get datasets, submit experiments, and monitor devices.
        """
        from sipyco.pc_rpc import Client
        try:
            self.scheduler = Client('::1', 3251, 'master_schedule')
            self.datasets = Client('::1', 3251, 'master_dataset_db')
        except Exception as e:
            print('ARTIQ Master not running. Scheduler and datasets disabled.')
        pass

    def _setVariables(self):
        """
        Sets ARTIQ-related variables.
        """
        # voltage_to_mu allows us to convert between voltage
        # and machine units (i.e. the value the device uses to
        # set the voltage).
        # We choose to do the conversion here instead of in the
        # API to minimize the overhead within the API (i.e. we
        # want the API to be as fast as possible).
        from artiq.coredevice.ad53xx import voltage_to_mu
        self.voltage_to_mu = voltage_to_mu

    def _setDevices(self):
        """
        Get the list of devices in the ARTIQ box.
        """
        # Get output TTLs.
        self.ttlout_list = list(self.api.ttlout_list.keys())
        # Get the type of DAC in the box (either Zotino or Fastino).
        # This is necessary since the API has different functions for
        # the two devices (see the API for more details).
        self.dacType = self.api.dacType


    # CORE
    @setting(11, "Get Devices", returns='*s')
    def getDevices(self, c):
        """
        Returns a list of ARTIQ devices.
        """
        return list(self.api.device_db.keys())

    # TTL
    @setting(111, "TTL Set", ttl_name='s', state=['b', 'i'], returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state. TTL can be of classes TTLOut or TTLInOut.
        Arguments:
            ttl_name    (str)           : name of the TTL.
            state       [bool, int]     : TTL power state (either True/False or 0/1).
        """
        # check that the TTL channel is valid
        if ttl_name not in self.ttlout_list:
            raise Exception('Error: device does not exist.')
        # check that input is valid
        if (type(state) == int) and (state not in (0, 1)):
            raise Exception('Error: invalid state.')
        # call the API function
        yield self.api.setTTL(ttl_name, state)


    # DAC
    @setting(211, "DAC Initialize", returns='')
    def initializeDAC(self, c):
        """
        Manually initialize the DAC.
        """
        yield self.api.initializeDAC()

    @setting(212, "DAC Set", dac_num='i', voltage='v', returns='')
    def setDAC(self, c, dac_num, voltage):
        """
        Manually set the voltage of a DAC channel.
        Arguments:
            dac_num     (int)   : the DAC channel number.
            voltage     (float) : the voltage (in V).
        """
        # check that dac channel is valid
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        # convert voltage (in V) to machine units (i.e. a register value)
        voltage_mu = int(self.dac_volt_to_mu(voltage))
        # check that voltage is valid
        if (voltage_mu < 0) or (voltage_mu > 0xffff):
            raise Exception('Error: invalid DAC voltage.')
        # call correct API function
        if self.dacType == 'Zotino':
            yield self.api.setZotino(dac_num, voltage_mu)
        elif self.dacType == 'Fastino':
            yield self.api.setFastino(dac_num, voltage_mu)

    @setting(213, "DAC Gain", dac_num='i', gain='v', returns='')
    def setDACGain(self, c, dac_num, gain):
        """
        Manually set the gain of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number.
            gain    (float) : the DAC channel gain (in %).
        """
        # gain adjustment is only for Zotino; not supported on Fastino
        if self.dacType != 'Zotino':
            raise Exception('Error: DAC does not support this function.')
        # check that dac channel is valid
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        # convert gain from a percentage to machine units (i.e. a register value)
        gain_mu = int(gain * 0xffff) - 1
        # check that gain is valid
        if (gain_mu < 0) or (gain_mu > 0xffff):
            raise Exception('Error: gain outside bounds of [0, 1].')
        # call API functions
        yield self.api.setZotinoGain(dac_num, gain_mu)


if __name__ == '__main__':
    from labrad import util
    util.runServer(ARTIQ_Server_Simple())
