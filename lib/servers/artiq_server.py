from labrad.server import LabradServer, setting


class ARTIQServer(LabradServer):
    """
    A server that uses devices from the ARTIQ box.
    """

    artiq_devices = {}

    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # check for artiq server
        try:
            self.artiq = cxn.artiq_server
            # get required devices
            for devices in self.artiq_devices.items():
                setattr(self, devices[0], devices[1])
        except Exception as e:
            print(e)
            raise


    # STATUS
    # todo: get artiq box details (ip address, name, device_db)


    # DMA
    @setting(222222, 'DMA', status='b', returns='b')
    def DMA(self, c, status=None):
        """
        Program the core DMA
        Arguments:
            status  (bool)  : whether to stop or start correction mode.
        Returns:
            status  (bool)  : whether to stop or start correction mode.
        """
        pass
    #todo: write setting to program DMA


    # EXPERIMENTS
    def runExperiment(self, file, args):
        """
        Run an experiment file.
        Arguments:
            file    (str)   : the location of the experiment file
            args    (str)   : the arguments to run the experiment with
        Returns:
                    ((str))  : the run parameters of the experiment.
        """
        pass
        #todo

    def schedule(self):
        """

        """
        pass
    #todo: check scheduling


    # DATA
    # todo: get dataset values
    # todo: create datasets