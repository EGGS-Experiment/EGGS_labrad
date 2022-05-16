from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QPushButton, QGridLayout, QHBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomGroupBox


class slider_gui(QFrame):

    def __init__(self):
        super().__init__()
        self.setFixedSize(250, 250)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Slider Client")
        self.makeLayout()

    def _makePositionWidget(self):
        position_widget = QWidget()
        position_widget_layout = QHBoxLayout(position_widget)

        self.position1 = TextChangingButton(("1", "1"))
        self.position2 = TextChangingButton(("2", "2"))
        self.position3 = TextChangingButton(("3", "3"))
        self.position4 = TextChangingButton(("4", "4"))
        self.position_buttons = {
            1: self.position1, 2: self.position2,
            3: self.position3, 4: self.position4
        }

        for widget in (self.position1, self.position2, self.position3, self.position4):
            widget.setFont(QFont('MS Shell Dlg 2', pointSize=20))
            position_widget_layout.addWidget(widget)

        position_widget_wrapped = QCustomGroupBox(position_widget, "Slider Position")
        return position_widget_wrapped

    def makeLayout(self):
        layout = QGridLayout(self)
        _BUTTON_FONT = QFont('MS Shell Dlg 2', pointSize=11)

        # title
        title = QLabel("Slider Client")
        title.setFont(QFont('MS Shell Dlg 2', pointSize=20))
        title.setAlignment(Qt.AlignCenter)

        # make widgets
        self.home_button = QPushButton("HOME")
        self.forward_button = QPushButton("+")
        self.backward_button = QPushButton("-")
        self.lockswitch = Lockswitch()
        self.lockswitch.toggled.connect(lambda status: self._lock(status))
        position_widget = self._makePositionWidget()

        # set font
        for widget in (self.home_button, self.lockswitch, self.forward_button, self.backward_button,):
            widget.setFont(_BUTTON_FONT)

        # lay out
        layout.addWidget(title,                         0, 0, 1, 4)
        layout.addWidget(self.home_button,              1, 0, 1, 2)
        layout.addWidget(self.lockswitch,               1, 2, 1, 2)
        layout.addWidget(position_widget,               2, 0, 2, 4)
        layout.addWidget(self.forward_button,           4, 0, 1, 2)
        layout.addWidget(self.backward_button,          4, 2, 1, 2)

    def _lock(self, status):
        self.position1.setEnabled(status)
        self.position2.setEnabled(status)
        self.position3.setEnabled(status)
        self.position4.setEnabled(status)
        self.forward_button.setEnabled(status)
        self.backward_button.setEnabled(status)
        self.home_button.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(slider_gui)
