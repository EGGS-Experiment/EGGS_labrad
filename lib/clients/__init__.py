#imports
from PyQt5.QtWidgets import QApplication
from twisted.internet import reactor
import qt5reactor
import sys

def runGUI(client):
    import sys
    app = QApplication(sys.argv)
    gui = client()
    try:
        gui.setupUi()
    except Exception as e:
        pass
    gui.show()
    app.exec_()

#
def runClient(client):
    app = QApplication([])
    qt5reactor.install()
    client = client(reactor)
    client.show()
    reactor.run()