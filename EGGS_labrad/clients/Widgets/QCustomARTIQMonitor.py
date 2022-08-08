from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel

__all__ = ['QCustomARTIQMonitor']


class QCustomARTIQMonitor(QFrame):
    """
    A widget that displays whether ARTIQ is currently running any experiments.
    """

    def __init__(self, parent):
        """
        Args:
            parent  (QWidget) : the parent GUI
        """
        super().__init__()

        # general setup
        self.parent = parent
        self.setFrameStyle(0x0001 | 0x0030)
        layout = QGridLayout(self)

        # widgets
        title = QLabel("Experiment Status")
        title.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        title.setAlignment(Qt.AlignCenter)
        self.status_display = QLabel('Clear')
        self.status_display.setStyleSheet('background-color: green')
        self.status_display.setAlignment(Qt.AlignCenter)

        # lay out
        layout.addWidget(title,         0, 0, 1, 1)
        layout.addWidget(self.status_display,   1, 0, 1, 1)

    def setStatus(self, status):
        """
        Enables/disables the GUI and sets the display.
        Args:
            status  (bool): whether an experiment is running.
        """
        if status:
            self.status_display.setText('Experiment Running')
            self.status_display.setStyleSheet('background-color: red')
            self.parent.setDisabled(status)
        else:
            self.parent.setDisabled(status)
            self.status_display.setText('Clear')
            self.status_display.setStyleSheet('background-color: green')
