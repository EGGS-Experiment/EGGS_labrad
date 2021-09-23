class SerialManagedServer(ManagedDeviceServer, SerialDeviceServer):
    """
    A server for a Seroal device.
     Creates a SerialDeviceWrapper for each device it finds that
     is appropriately named.  Provides standard settings for listing
     devices, selecting a device for the current context, and
     refreshing the list of devices.  Also, allows us to read from,
     write to, and query the selected GPIB device directly.
     """

class SerialDeviceWrapper(DeviceWrapper):