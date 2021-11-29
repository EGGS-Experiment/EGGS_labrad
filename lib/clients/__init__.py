"""
Contains stuff useful for LabRAD clients
"""

#imports
import sys

from PyQt5.QtWidgets import QApplication

__all__ = ["runGUI", "runClient"]

#run functions
def runGUI(client, **kwargs):
    """
    Runs a LabRAD GUI file written using PyQt5
    """
    #widgets require a QApplication to run
    app = QApplication(sys.argv)
    #instantiate gui
    gui = client(**kwargs)
    #set up UI if needed
    try:
        gui.setupUi()
    except Exception as e:
        print('No need to setup UI')
    #run GUI file
    gui.show()
    sys.exit(app.exec())

def runClient(client, **kwargs):
    """
    Runs a LabRAD client written using PyQt5
    """
    #widgets require a QApplication to run
    app = QApplication([])
    #reactor may already be installed
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
    #instantiate client with a reactor
    from twisted.internet import reactor
    client = client(reactor, **kwargs)
    #show client
    try:
        #client.gui.showMaximized()
        client.gui.show()
    except:
        #client.showMaximized()
        client.show()
    #start reactor
    reactor.run()
    #run on exit
    try:
        client.close()
    except:
        sys.exit(app.exec())

