import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout
from PyQt5.QtGui import QIcon
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.lib.clients.Widgets import DetachableTabWidget

class EGGS_gui(QMainWindow):

    name = 'EGGS GUI'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard, parent=None):
        super(EGGS_gui, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout(self.cxn)
        self.setWindowIcon(QIcon('/eggs.png'))
        self.setWindowTitle('EGGS GUI')

    @inlineCallbacks
    def connect(self):
        # from labrad.wrappers import connectAsync
        # self.cxn = yield connectAsync('localhost', name=self.name, password=self.LABRADPASSWORD)
        # self.dv = self.cxn.data_vault
        # self.reg = self.cxn.registry
        from EGGS_labrad.lib.clients.connection import connection
        self.cxn = connection(name=self.name)
        yield self.cxn.connect()

    def makeLayout(self, cxn):
        #central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        #create subwidgets
        script_scanner = self.makeScriptScannerWidget(reactor, cxn)
        cryo = self.makeCryoWidget(reactor)

        #create tabs for each subwidget
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryo, '&Cryo')
        #self.tabWidget.addTab(cryovac, '&Trap')

        #put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn = cxn)
        return scriptscanner

    def makeCryoWidget(self, reactor):
        from EGGS_labrad.lib.clients.cryovac_clients.lakeshore_client import lakeshore_client
        from EGGS_labrad.lib.clients.cryovac_clients.niops03_client import niops03_client
        from EGGS_labrad.lib.clients.cryovac_clients.twistorr74_client import twistorr74_client
        lakeshore = lakeshore_client(reactor)
        niops = niops03_client(reactor)
        twistorr = twistorr74_client(reactor)

        #main layout
        holder_widget = QWidget()
        holder_layout = QGridLayout()
        holder_widget.setLayout(holder_layout)
        holder_layout.addWidget(lakeshore, 0, 0, 2, 2)
        holder_layout.addWidget(niops, 0, 2, 1, 1)
        holder_layout.addWidget(twistorr, 1, 2, 1, 1)
        holder_layout.setColumnStretch(0, 1)
        holder_layout.setColumnStretch(1, 1)
        holder_layout.setColumnStretch(2, 1)
        holder_layout.setRowStretch(0, 1)
        holder_layout.setRowStretch(1, 1)
        holder_layout.setRowStretch(2, 1)
        #todo: try size policy
        return holder_widget

    def makeTrapWidget(self, reactor):
        from EGGS_labrad.lib.clients.rf_client.lakeshore_client import rf_client
        rf_widget = rf_client(reactor)
        return rf_widget

    def closeEvent(self, x):
        self.reactor.stop()


if __name__=="__main__":
    import sys, qt5reactor
    app = QApplication(sys.argv)
    clipboard = app.clipboard()
    qt5reactor.install()
    from twisted.internet import reactor
    EGGSGUI = EGGS_gui(reactor, clipboard)
    EGGSGUI.show()
    reactor.run()
