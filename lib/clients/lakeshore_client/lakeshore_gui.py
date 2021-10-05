# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'lakeshore_gui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LAKESHORE_UI(object):
    def setupUi(self, LAKESHORE_UI):
        LAKESHORE_UI.setObjectName("LAKESHORE_UI")
        LAKESHORE_UI.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(LAKESHORE_UI)
        self.centralwidget.setObjectName("centralwidget")
        self.button_open = QtWidgets.QPushButton(self.centralwidget)
        self.button_open.setGeometry(QtCore.QRect(210, 60, 75, 23))
        self.button_open.setObjectName("button_open")
        self.editor_window = QtWidgets.QTextEdit(self.centralwidget)
        self.editor_window.setGeometry(QtCore.QRect(230, 220, 104, 71))
        self.editor_window.setObjectName("editor_window")
        LAKESHORE_UI.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(LAKESHORE_UI)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        LAKESHORE_UI.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(LAKESHORE_UI)
        self.statusbar.setObjectName("statusbar")
        LAKESHORE_UI.setStatusBar(self.statusbar)

        self.retranslateUi(LAKESHORE_UI)
        self.button_open.clicked.connect(self.editor_window.close)
        QtCore.QMetaObject.connectSlotsByName(LAKESHORE_UI)

    def retranslateUi(self, LAKESHORE_UI):
        _translate = QtCore.QCoreApplication.translate
        LAKESHORE_UI.setWindowTitle(_translate("LAKESHORE_UI", "MainWindow"))
        self.button_open.setText(_translate("LAKESHORE_UI", "PushButton"))

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = Ui_LAKESHORE_UI()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

