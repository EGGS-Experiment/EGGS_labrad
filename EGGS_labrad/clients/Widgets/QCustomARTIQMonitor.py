from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel

__all__ = ['QCustomARTIQMonitor']


class QCustomARTIQMonitor(QFrame):
    """
    A widget that displays whether ARTIQ is currently running any experiments.
    Arguments:
        parent  (QWidget) : the parent GUI
    """

    def __init__(self, parent):
        super().__init__()

        # general setup
        self.parent = parent
        self.setFrameStyle(0x0001 | 0x0030)
        layout = QGridLayout(self)

        # widgets
        title = QLabel("Exp. Status")
        title.setFont(QFont('MS Shell Dlg 2', pointSize=11))
        title.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.status_display = QLabel('CLEAR')
        self.status_display.setStyleSheet('background-color: green; color: white')
        self.status_display.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.status_display.setFont(QFont('MS Shell Dlg 2', pointSize=13))

        # lay out
        layout.addWidget(title,                 0, 0, 1, 1)
        layout.addWidget(self.status_display,   1, 0, 1, 1)

    def setStatus(self, msg):
        """
        Enables/disables the GUI and sets the display.
        Arguments:
            msg  (bool, int): the run status and experiment RID (if running).
        """
        status, rid = msg
        if status:
            self.status_display.setText('RID: {}'.format(rid))
            self.status_display.setStyleSheet('background-color: red')
            self.status_display.adjustSize()
            self.parent.setDisabled(status)
        else:
            self.parent.setDisabled(status)
            self.status_display.setText('CLEAR')
            self.status_display.setStyleSheet('background-color: green')
