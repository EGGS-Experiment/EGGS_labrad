from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout
from PyQt5.QtGui import QIcon
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.lib.clients.Widgets import DetachableTabWidget

class EGGS_GUI(QMainWindow):

    name = 'EGGS GUI'

    def __init__(self, reactor, clipboard, parent=None):
        super(EGGS_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout(self.cxn)

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
        script_scanner = self.makeScriptScannerWidget(reactor, cxn)
        cryo = self.makeCryoWidget(reactor)

        #create tabs for each subwidget
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryo, '&Cryo')
        #self.tabWidget.addTab(cryo, '&Trap')

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
        from EGGS_labrad.lib.clients.cryo_clients.lakeshore_client import lakeshore_client
        from EGGS_labrad.lib.clients.cryo_clients.niops03_client import niops03_client
        from EGGS_labrad.lib.clients.cryo_clients.twistorr74_client import twistorr74_client
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
    a = QApplication(sys.argv)
    clipboard = a.clipboard()
    qt5reactor.install()
    from twisted.internet import reactor
    EGGSGUI = EGGS_GUI(reactor, clipboard)
    EGGSGUI.setWindowIcon(QIcon('C:/Users/EGGS1/Documents/Code/EGGS_labrad/lib/eggs.png'))
    EGGSGUI.setWindowTitle('EGGS GUI')
    EGGSGUI.show()
    reactor.run()
