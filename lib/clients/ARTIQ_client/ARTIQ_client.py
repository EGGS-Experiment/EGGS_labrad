from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTabWidget

from twisted.internet.defer import inlineCallbacks


class ARTIQ_client(QMainWindow):

    name = 'ARTIQ Client'

    def __init__(self, reactor, clipboard=None, parent=None):
        super(ARTIQ_client, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.setWindowTitle(self.name)
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
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        # create subwidgets
        ttl_widget = yield self.makeTTLWidget()
        dds_widget = yield self.makeDDSWidget()
        dac_widget = yield self.makeDACWidget()
        adc_widget = yield self.makeADCWidget()

        # create tabs for each subwidget
        self.tabWidget.addTab(ttl_widget, '&TTL')
        self.tabWidget.addTab(dds_widget, '&DDS')
        self.tabWidget.addTab(dac_widget, '&DAC')
        self.tabWidget.addTab(adc_widget, '&ADC')

        # put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeTTLWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.TTL_client import TTL_client
        return TTL_client(self.reactor, self.cxn)

    def makeDDSWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import DDS_client
        return DDS_client(self.reactor, self.cxn)

    def makeDACWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.DAC_client import DAC_client
        return DAC_client(self.reactor, self.cxn)

    def makeADCWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.ADC_client import ADC_client
        return ADC_client(self.reactor, self.cxn)

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(ARTIQ_client)

