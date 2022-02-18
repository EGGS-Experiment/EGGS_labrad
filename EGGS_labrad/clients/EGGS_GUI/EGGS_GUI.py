import os

from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout


class EGGS_gui(QMainWindow):

    name = 'EGGS GUI'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard=None, parent=None):
        super(EGGS_gui, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.setWindowTitle('EGGS GUI')
        self.setWindowIcon(QIcon('/eggs.png'))
        # connect devices synchronously
        d = self.connect()
        d.addCallback(self.makeLayout)

    @inlineCallbacks
    def connect(self):
        from EGGS_labrad.clients.connect import connection
        self.cxn = connection(name=self.name)
        yield self.cxn.connect()
        return self.cxn

    def makeLayout(self, cxn):
        # central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()
        # create subwidgets
        script_scanner = self.makeScriptScannerWidget(self.reactor, cxn)
        cryovac = self.makeCryovacWidget(self.reactor, cxn)
        trap = self.makeTrapWidget(self.reactor, cxn)
        lasers = self.makeLaserWidget(self.reactor, cxn)
        imaging = self.makeImagingWidget(self.reactor, cxn)
        # create tabs for each subwidget
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryovac, '&Cryovac')
        self.tabWidget.addTab(trap, '&Trap')
        self.tabWidget.addTab(lasers, '&Lasers')
        self.tabWidget.addTab(imaging, '&Imaging')
        # put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.clients.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn=cxn)
        return scriptscanner

    def makeCryovacWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.cryovac_clients.lakeshore336_client import lakeshore336_client
        from EGGS_labrad.clients.cryovac_clients.niops03_client import niops03_client
        from EGGS_labrad.clients.cryovac_clients.twistorr74_client import twistorr74_client
        from EGGS_labrad.clients.cryovac_clients.RGA_client import RGA_client
        from EGGS_labrad.clients.cryovac_clients.fma1700a_client import fma1700a_client
        #from EGGS_labrad.clients.cryovac_clients.f70_client import f70_client
        clients = {lakeshore336_client: (0, 0), RGA_client: (0, 1), twistorr74_client: (0, 2),
                   niops03_client: (1, 1), fma1700a_client: (1, 2)}
        return self._createTabLayout(clients, reactor, cxn)

    def makeTrapWidget(self, reactor, cxn):
        from EGGS_labrad.clients.trap_clients.rf_client import rf_client
        from EGGS_labrad.clients.trap_clients.DC_client import DC_client
        clients = {rf_client: (0, 0), DC_client: (0, 1)}
        return self._createTabLayout(clients, reactor, cxn)

    def makeLaserWidget(self, reactor, cxn):
        from EGGS_labrad.clients.SLS_client.SLS_client import SLS_client
        #from EGGS_labrad.clients.shutter_client import shutter_client
        clients = {SLS_client: (0, 0)}
        return self._createTabLayout(clients, reactor, cxn)

    def makeImagingWidget(self, reactor, cxn):
        from EGGS_labrad.clients.PMT_client.PMT_client import PMT_client
        clients = {PMT_client: (0, 0)}
        return self._createTabLayout(clients, reactor, cxn)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()

    def _createTabLayout(self, clientDict, reactor, cxn):
        """
        Creates a tab widget from constituent widgets stored in a dictionary.
        """
        holder_widget = QWidget()
        holder_layout = QGridLayout()
        holder_widget.setLayout(holder_layout)
        for client, position in clientDict.items():
            client_tmp = client(reactor, cxn=cxn.cxn)
            try:
                if hasattr(client_tmp, 'getgui'):
                    holder_layout.addWidget(client_tmp.getgui(), *position)
                elif hasattr(client_tmp, 'gui'):
                    holder_layout.addWidget(client_tmp.gui, *position)
            except Exception as e:
                print(e)
        return holder_widget


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(EGGS_gui)
