from os import environ, path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton


class QClientHeader(QFrame):
    """
    A basic client header that shows the client name and has
    a restart button to allow restarts.
    """

    def __init__(self, name, serial=False, polling=False):
        super().__init__()
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self._makeHeader()
        if serial == True:
            self._makeSerial()
        if polling == True:
            self._makePolling()

    def _makeHeader(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QHBoxLayout(self)
        # title
        self.title = QLabel(self.name)
        self.title.setFont(QFont(shell_font, pointSize=15))
        self.title.setAlignment(Qt.AlignCenter)
        # restart button
        self.restartbutton = QPushButton()
        # set restart button icon
        path_root = environ['EGGS_LABRAD_ROOT']
        icon_path = path.join(path_root, 'EGGS_labrad\\clients\\Widgets\\refresh.png')
        self.restartbutton.setIcon(QIcon(icon_path))
        # lay out
        layout.addWidget(self.title)
        layout.addWidget(self.restartbutton)
        # set fixed size
        self.setMinimumSize(1.8 * self.title.sizeHint())

    def _makeSerial(self):
        pass

    def _makePolling(self):
        pass
