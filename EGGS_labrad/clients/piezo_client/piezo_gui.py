from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomUnscrollableSpinBox, Lockswitch


class piezo_gui(QFrame):
    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(350, 275)
        self.setWindowTitle("Piezo Client")
        self.makeWidgets()

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QGridLayout(self)

        # title
        self.title = QLabel('AMO3 Piezo Client')
        self.title.setFont(QFont(shell_font, pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title,    0, 0, 1, 2)

        # create channel widgets
        self.channels = list()
        for i in range(4):
            # create and configure channel widget
            channel_widget = QFrame()
            channel_widget.setFrameStyle(0x0001 | 0x0030)
            channel_widget_layout = QGridLayout(channel_widget)

            channel_title = QLabel("Channel {:d}".format(i + 1))
            channel_title.setFont(QFont(shell_font, pointSize=10))
            channel_title.setAlignment(Qt.AlignCenter)

            channel_widget.voltage = QCustomUnscrollableSpinBox()
            channel_widget.voltage.setRange(0, 15)
            channel_widget.voltage.setDecimals(2)
            channel_widget.voltage.setSingleStep(1)
            channel_widget.voltage.setKeyboardTracking(False)
            channel_widget.voltage.setFont(QFont(shell_font, pointSize=12))
            channel_widget.voltage.setAlignment(Qt.AlignRight)

            channel_widget.toggleswitch = TextChangingButton(("On", "Off"))
            channel_widget.lockswitch = Lockswitch()
            channel_widget.lockswitch.clicked.connect(lambda status, _chan=i: self._lock(_chan, status))

            # lay out channel
            channel_widget_layout.addWidget(channel_title,                  0, 0, 1, 2)
            channel_widget_layout.addWidget(channel_widget.voltage,         1, 0, 1, 2)
            channel_widget_layout.addWidget(channel_widget.toggleswitch,    2, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.lockswitch,      2, 1, 1, 1)

            # add channel to holder
            self.channels.append(channel_widget)
            layout.addWidget(channel_widget, 1 + i // 2, i % 2, 1, 1)

    def _lock(self, channel_num, status):
        channel_widget = self.channels[channel_num]
        channel_widget.voltage.setEnabled(status)
        channel_widget.toggleswitch.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(piezo_gui)
