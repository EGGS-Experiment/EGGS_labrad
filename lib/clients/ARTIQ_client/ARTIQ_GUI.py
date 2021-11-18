from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget

from twisted.internet.defer import inlineCallbacks, returnValue


class ARTIQ_gui(QMainWindow):

    name = 'ARTIQ GUI'

    def __init__(self, reactor, clipboard, parent=None):
        super(ARTIQ_gui, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout(self.cxn)
        self.setWindowTitle(self.name)

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name=self.name)
        #check that required servers are online
        try:
            self.dv = self.cxn.data_vault
            self.reg = self.cxn.registry
        except Exception as e:
            print(e)
            raise

    def makeLayout(self, cxn):
        #central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        #create subwidgets
        ttl_widget = self.makeTTLWidget(reactor, cxn)
        dds_widget = self.makeDDSWidget(reactor, cxn)
        dac_widget = self.makeDACWidget(reactor, cxn)

        #create tabs for each subwidget
        self.tabWidget.addTab(ttl_widget, '&TTL')
        self.tabWidget.addTab(dds_widget, '&DDS')
        self.tabWidget.addTab(dac_widget, '&DAC')

        #put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeTTLWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.ARTIQ_client.TTL_client import TTL_client
        return TTL_client(reactor, cxn)

    def makeDDSWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import DDS_client
        return DDS_client(reactor, cxn)

    def makeDACWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import DAC_client
        return DAC_client(reactor, cxn)

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    import sys
    app = QApplication(sys.argv)
    clipboard = app.clipboard()
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    gui = ARTIQ_gui(reactor, clipboard)
    gui.show()
    reactor.run()
    app.exec_()
