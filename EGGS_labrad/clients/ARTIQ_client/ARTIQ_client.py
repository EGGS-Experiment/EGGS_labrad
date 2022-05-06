from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout

from twisted.internet.defer import inlineCallbacks


class ARTIQ_client(QMainWindow):

    name = 'ARTIQ Client'

    def __init__(self, reactor, clipboard=None, parent=None):
        super(ARTIQ_client, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.setWindowTitle(self.name)
        # set window icon
        self.setWindowIcon(QIcon("labart_icon.JPG"))
        d = self.connect()
        d.addCallback(self.makeLayout)

    @inlineCallbacks
    def connect(self):
        import os
        LABRADHOST = os.environ['LABRADHOST']
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        # check that required servers are online
        try:
            self.dv = yield self.cxn.data_vault
            self.reg = yield self.cxn.registry
        except Exception as e:
            print(e)
            raise
        return self.cxn

    @inlineCallbacks
    def makeLayout(self, cxn):
        # central layout
        centralWidget = QWidget()
        layout = QHBoxLayout(centralWidget)
        self.tabWidget = QTabWidget()
        self.tabWidget.setMovable(True)
        # create subwidgets
        ttl_widget = yield self.makeTTLWidget(self.reactor, cxn)
        dds_widget = yield self.makeDDSWidget(self.reactor, cxn)
        dac_widget = yield self.makeDACWidget(self.reactor, cxn)
        adc_widget = yield self.makeADCWidget(self.reactor, cxn)
        # create tabs for each subwidget
        self.tabWidget.addTab(ttl_widget, '&TTL')
        self.tabWidget.addTab(dds_widget, '&DDS')
        self.tabWidget.addTab(dac_widget, '&DAC')
        self.tabWidget.addTab(adc_widget, '&ADC')
        # put it all together
        layout.addWidget(self.tabWidget)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeTTLWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.TTL_client import TTL_client
        clients = {TTL_client: {"pos": (0, 0)}}
        return self._createTabLayout(clients, reactor, cxn)

    def makeDDSWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.DDS_client import DDS_client
        clients = {DDS_client: {"pos": (0, 0)}}
        return self._createTabLayout(clients, reactor, cxn)

    def makeDACWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.DAC_client import DAC_client
        clients = {DAC_client: {"pos": (0, 0)}}
        return self._createTabLayout(clients, reactor, cxn)

    def makeADCWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.ADC_client import ADC_client
        clients = {ADC_client: {"pos": (0, 0)}}
        return self._createTabLayout(clients, reactor, cxn)

    def _createTabLayout(self, clientDict, reactor, cxn=None):
        """
        Creates a tab widget from constituent widgets stored in a dictionary.
        """
        holder_widget = QWidget()
        holder_layout = QGridLayout(holder_widget)
        for client, config in clientDict.items():
            # get configuration settings for each client
            position = config["pos"]
            args, kwargs = ((), {})
            try:
                args = config["args"]
            except KeyError:
                pass
            try:
                kwargs = config["kwargs"]
            except KeyError:
                pass
            # start up client
            try:
                client_tmp = client(reactor, cxn=cxn, *args, **kwargs)
            except Exception as e:
                print(client, e)
            try:
                if hasattr(client_tmp, 'getgui'):
                    holder_layout.addWidget(client_tmp.getgui(), *position)
                elif hasattr(client_tmp, 'gui'):
                    print('hsagui')
                    holder_layout.addWidget(client_tmp.gui, *position)
            except Exception as e:
                print(e)
        return holder_widget

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(ARTIQ_client)

