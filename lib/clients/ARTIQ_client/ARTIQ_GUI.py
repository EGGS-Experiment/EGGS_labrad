from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget

from twisted.internet.defer import inlineCallbacks, returnValue


class ARTIQ_gui(QMainWindow):

    name = 'ARTIQ GUI'

    def __init__(self, reactor, clipboard=None, parent=None):
        super(ARTIQ_gui, self).__init__(parent)
        #self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout()
        self.setWindowTitle(self.name)

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name=self.name)
        #check that required servers are online
        try:
            self.dv = yield self.cxn.data_vault
            self.reg = yield self.cxn.registry
        except Exception as e:
            print(e)
            raise

    @inlineCallbacks
    def makeLayout(self):
        #central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        #create subwidgets
        ttl_widget = yield self.makeTTLWidget()
        dds_widget = yield self.makeDDSWidget()
        dac_widget = yield self.makeDACWidget()

        #create tabs for each subwidget
        self.tabWidget.addTab(ttl_widget, '&TTL')
        self.tabWidget.addTab(dds_widget, '&DDS')
        self.tabWidget.addTab(dac_widget, '&DAC')

        #put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeTTLWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.TTL_client import TTL_client
        return TTL_client(self.reactor)

    def makeDDSWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import DDS_client
        return DDS_client(self.reactor)

    def makeDACWidget(self):
        from EGGS_labrad.lib.clients.ARTIQ_client.DAC_client import DAC_client
        return DAC_client(self.reactor)

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    # from EGGS_labrad.lib.clients import runClient
    # runClient(ARTIQ_gui)
    import sys
    app = QApplication(sys.argv)
    clipboard = app.clipboard()
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    gui = ARTIQ_gui(reactor)
    gui.show()
    reactor.run()
    app.exec_()
