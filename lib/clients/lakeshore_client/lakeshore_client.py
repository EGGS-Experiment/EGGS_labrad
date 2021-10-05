import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from lakeshore_gui import Ui_notepad
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.lib.clients.lakeshore_client import LAKESHORE_GUI

class LAKESHORE_CLIENT(LAKESHORE_GUI):
    def __init__(self, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_notepad()
        self.ui.setupUi(self)
        self.ui.button_open.clicked.connect(self.file_dialog)
        self.ui.button_save.clicked.connect(self.file_save)


    #connections
    @inlineCallbacks
    def connect(self, host_name, client_name):
        """connect labrad server"""

    #setup functions

    #button functions
    def lock_device(self):
        """prevent changes to device"""

    #GUI update functions
    def update_temp(self):
        """update display"""


    #Lakeshore functions
    @inlineCallbacks
    def read_temperature(self, channel):
        """get temp"""

    @inlineCallbacks
    def set_heater(self):
        """set heater"""

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = StartQt5()
    myapp.show()
    sys.exit(app.exec_())