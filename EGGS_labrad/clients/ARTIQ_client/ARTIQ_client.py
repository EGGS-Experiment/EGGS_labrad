from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTabWidget

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.Widgets import QDetachableTabWidget


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
        return self.cxn

    def makeLayout(self, cxn):
        # central layout
        centralWidget = QWidget()
        layout = QHBoxLayout(centralWidget)
        self.tabWidget = QDetachableTabWidget()
        #self.tabWidget.setMovable(True)
        # create subwidgets
        ttl_widget = self.makeTTLWidget(self.reactor, cxn)
        dds_widget = self.makeDDSWidget(self.reactor, cxn)
        dac_widget = self.makeDACWidget(self.reactor, cxn)
        adc_widget = self.makeADCWidget(self.reactor, cxn)
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
        client_tmp = TTL_client(reactor, cxn)
        return client_tmp

    def makeDDSWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.DDS_client import DDS_client
        client_tmp = DDS_client(reactor, cxn)
        return client_tmp

    def makeDACWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.DAC_client import DAC_client
        client_tmp = DAC_client(reactor, cxn)
        return client_tmp

    def makeADCWidget(self, reactor, cxn):
        from EGGS_labrad.clients.ARTIQ_client.ADC_client import ADC_client
        client_tmp = ADC_client(reactor, cxn)
        return client_tmp

    def closeEvent(self, x):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    # set up logging
    from sys import stdout
    from twisted.python import log
    log.startLogging(stdout)
    # set up qapplication
    app = QApplication([])
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
    # instantiate client with a reactor
    from twisted.internet import reactor
    client_tmp = ARTIQ_client(reactor)
    # show gui
    client_tmp.showMaximized()
    # start reactor
    reactor.callWhenRunning(app.exec)
    reactor.addSystemEventTrigger('after', 'shutdown', client_tmp.close)
    reactor.runReturn()
    # close client on exit
    try:
        client_tmp.close()
    except Exception as e:
        print(e)

