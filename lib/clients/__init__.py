#imports
from PyQt5.QtWidgets import QApplication
from twisted.internet import reactor
import sys

def runGUI(client):
    """

    """
    app = QApplication(sys.argv)
    gui = client()
    try:
        gui.setupUi()
    except Exception as e:
        print('thkim')
    gui.show()
    app.exec_()

#
def runClient(client):
    """

    """
    import qt5reactor
    app = QApplication([])
    qt5reactor.install()
    client = client(reactor)
    client.show()
    reactor.run()