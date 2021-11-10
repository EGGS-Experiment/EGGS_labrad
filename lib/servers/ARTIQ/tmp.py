class ARTIQ_api_exp(EnvExperiment):
    """
    Instantiates the API and uses it as the target for a server.
    """
    def build(self):
        self.targets = {
            'device': ARTIQ_api(self)
        }
        self.loop = get_event_loop()
        self.server = Server(self.targets, description=None, builtin_terminate=True, allow_parallel=True)

    def run(self):
        self.loop.run_until_complete(self.server.start('::1', 8888))
        try:
            self.loop.run_until_complete(self.server.wait_terminate())
        finally:
            self.loop.run_until_complete(self.server.stop())
            self.loop.close()


    @setting(1, 'Connect ARTIQ', host='s', port='s', returns='')
    def connectARTIQ(self, c, port, host='::1'):
        """
        Connect to a SiPyCo server that .
        Argument:
            host    (string): the ARTIQ server host
            port    (string): the ARTIQ server TCP port
        """
        if self.artiq:
            raise Exception('Already connected to ARTIQ')
        self.artiq = Client(host, port, 'device')

    @setting(2, 'Disconnect ARTIQ', returns='')
    def disconnectARTIQ(self, c):
        """Connect to the ARTIQ box."""
        if not self.api:
            raise Exception('Not connected to ARTIQ')
        self.api.close_rpc()
        self.api = None