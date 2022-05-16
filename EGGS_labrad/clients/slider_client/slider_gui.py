from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QPushButton, QGridLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox

_SHELL_FONT = 'MS Shell Dlg 2'


class slider_gui(QFrame):

    def __init__(self):
        super().__init__()
        self.setFixedSize(540, 520)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Slider Client")
        self.makeLayout()

    def makeLayout(self):
        layout = QGridLayout(self)
        button_font = QFont('MS Shell Dlg 2', pointSize=11)

        # title
        title = QLabel("Slider Client")
        title.setFont(QFont('MS Shell Dlg 2', pointSize=20))
        title.setAlignment(Qt.AlignCenter)

        # make widgets
        self.home_button = QPushButton("HOME")
        self.lockswitch = Lockswitch()
        self.forward_button = QPushButton("+")
        self.backward_button = QPushButton("-")
        self.position1 = TextChangingButton(("1", "1"))
        self.position2 = TextChangingButton(("2", "2"))
        self.position3 = TextChangingButton(("3", "3"))
        self.position4 = TextChangingButton(("4", "4"))
        for widget in (self.home_button, self.lockswitch, self.forward_button, self.backward_button,
                       self.position1, self.position2, self.position3, self.position4):
            widget.setFont(button_font)

        # lay out
        layout.addWidget(title,                         0, 0, 1, 4)
        layout.addWidget(self.home_button,              1, 0, 1, 2)
        layout.addWidget(self.lockswitch,               1, 2, 1, 2)
        layout.addWidget(self.position1,                2, 0, 1, 1)
        layout.addWidget(self.position2,                2, 1, 1, 1)
        layout.addWidget(self.position3,                2, 2, 1, 1)
        layout.addWidget(self.position4,                2, 3, 1, 1)
        layout.addWidget(title,                         3, 0, 1, 2)
        layout.addWidget(title,                         3, 2, 1, 2)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(slider_gui)
