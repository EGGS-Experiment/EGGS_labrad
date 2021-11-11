import sys
from PyQt5.QtWidgets import QWidget, QApplication
from cryo import Ui_cryo_gui

class cryo_gui(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.ui=Ui_cryo_gui()
        self.ui.setupUi(self)


if __name__=="__main__":
    app = QApplication(sys.argv)
    gui = cryo_gui()
    gui.show()
    app.exec_()