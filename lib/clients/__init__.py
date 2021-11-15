#imports
from PyQt5.QtWidgets import QApplication
import sys

def runGUI(client):
    """
    Runs a LabRAD GUI file written using PyQt5
    """
    #widgets require a QApplication to run
    app = QApplication(sys.argv)
    #instantiate gui
    gui = client()
    #set up UI if needed
    try:
        gui.setupUi()
    except Exception as e:
        print('No need to setup UI')
    #run GUI file
    gui.show()
    app.exec_()

#
def runClient(client):
    """
    Runs a LabRAD client written using PyQt5
    """
    #widgets require a QApplication to run
    app = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    #instantiate a client with a reactor
    client = client(reactor)
    #show client
    client.show()
    #start reactor
    reactor.run()