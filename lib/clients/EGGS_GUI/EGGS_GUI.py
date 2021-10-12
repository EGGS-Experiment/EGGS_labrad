from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout
from PyQt5.QtGui import QIcon
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.lib.clients.Widgets.detachable_tab import DetachableTabWidget

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
        self.cxn = connection(name = self.name)
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

        #put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn = cxn)
        return scriptscanner

    def makeCryoWidget(self, reactor):
        from EGGS_labrad.lib.clients.lakeshore_client.lakeshore_client import lakeshore_client
        from EGGS_labrad.lib.clients.pump_client.pump_client import pump_client
        lakeshore = lakeshore_client(reactor)
        pumps = pump_client(reactor)

        #main layout
        holder_widget = QWidget()
        holder_layout = QGridLayout()
        holder_widget.setLayout(holder_layout)
        holder_layout.addWidget(lakeshore, 0, 0, 2, 3)
        holder_layout.addWidget(pumps, 0, 3, 1, 1)
        #todo: try size policy
        return holder_widget

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
