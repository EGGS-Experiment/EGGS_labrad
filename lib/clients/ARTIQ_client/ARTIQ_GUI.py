from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout

from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.clients.Widgets import DetachableTabWidget

class ARTIQ_GUI(QMainWindow):

    name = 'ARTIQ GUI'

    def __init__(self, reactor, clipboard, parent=None):
        super(ARTIQ_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout(self.cxn)
        self.setWindowTitle(name)

    @inlineCallbacks
    def connect(self):
        from EGGS_labrad.lib.clients.connection import connection
        self.cxn = connection(name=self.name)
        yield self.cxn.connect()

    def makeLayout(self, cxn):
        #central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        #create subwidgets
        dds_widget = self.makeDDSWidget(reactor, cxn)
        ttl_widget = self.makeTTLWidget(reactor)
        #dac_widget = self.makeDACWidget(reactor)

        #create tabs for each subwidget
        self.tabWidget.addTab(ttl_widget, '&TTL')
        self.tabWidget.addTab(dds_widget, '&DDS')
        #self.tabWidget.addTab(dds_widget, '&DAC')

        #put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeDDSWidget(self, reactor, cxn):
        from EGGS_labrad.lib.servers.ARTIQ.device_db import device_db
        dds_list = []
        for device_name, device_params in device_db.items():
            try:
                if device_params['class'] == 'AD9910':
                    dds_list.append(device_name)
            except KeyError:
                continue
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import AD9910_channels
        dds_widget = AD9910_channels(reactor, channels=dds_list)
        return dds_widget

    def makeDDSWidget(self, reactor, cxn):
        from EGGS_labrad.lib.servers.ARTIQ.device_db import device_db
        dds_list = []
        for device_name, device_params in device_db.items():
            try:
                if device_params['class'] == 'AD9910':
                    dds_list.append(device_name)
            except KeyError:
                continue
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import DDS_client
        dds_widget = DDS_client(reactor, channels=dds_list)
        return dds_widget

    def makeDACWidget(self, reactor, cxn):
        from EGGS_labrad.lib.servers.ARTIQ.device_db import device_db
        dds_list = []
        for device_name, device_params in device_db.items():
            try:
                if device_params['class'] == 'AD9910':
                    dds_list.append(device_name)
            except KeyError:
                continue
        from EGGS_labrad.lib.clients.ARTIQ_client.DDS_client import AD9910_channels
        dds_widget = DAC_client(reactor, channels=dds_list)
        return dds_widget

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    import sys, qt5reactor
    app = QApplication(sys.argv)
    clipboard = app.clipboard()
    qt5reactor.install()
    from twisted.internet import reactor
    gui = ARTIQ_GUI(reactor, clipboard)
    gui.show()
    reactor.run()
