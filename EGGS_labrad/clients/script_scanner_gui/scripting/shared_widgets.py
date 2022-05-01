"""
Contains custom widgets that are shared between different GUIs
"""
from PyQt5 import QtCore, QtWidgets

__all__ = ["fixed_width_button", "progress_bar"]
# todo: try to use QProgressBar instead


class fixed_width_button(QtWidgets.QPushButton):
    def __init__(self, text, size):
        super(fixed_width_button, self).__init__(text)
        self.size = size
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def sizeHint(self):
        return QtCore.QSize(*self.size)


class progress_bar(QtWidgets.QProgressBar):
    def __init__(self, reactor, parent=None):
        super(progress_bar, self).__init__(parent)
        self.reactor = reactor
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.set_status('', 0.0)

    def set_status(self, status_name, percentage):
        self.setValue(percentage)
        self.setFormat('{0} %p%'.format(status_name))

    def closeEvent(self, x):
        self.reactor.stop()