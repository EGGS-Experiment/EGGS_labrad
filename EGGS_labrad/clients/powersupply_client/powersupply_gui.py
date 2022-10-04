from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomUnscrollableSpinBox, Lockswitch


class powersupply_gui(QFrame):
    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        #self.setFixedSize(350, 275)
        self.setWindowTitle("Power Supply Client")
        self.makeWidgets()

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QGridLayout(self)

        # title
        self.title = QLabel('Power Supply Client')
        self.title.setFont(QFont(shell_font, pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title,    0, 0, 1, 2)

        # create channel widgets
        self.channels = list()
        for i in range(3):
            # create and configure channel widget
            channel_widget = QFrame()
            channel_widget.setFrameStyle(0x0001 | 0x0030)
            channel_widget_layout = QGridLayout(channel_widget)

            channel_title = QLabel("Channel {:d}".format(i + 1))
            channel_title.setFont(QFont(shell_font, pointSize=8))
            channel_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)

            # GENERAL
            channel_widget.toggleswitch = TextChangingButton(("On", "Off"))
            channel_widget.lockswitch = Lockswitch()
            channel_widget.lockswitch.clicked.connect(lambda status, _chan=i: self._lock(_chan, status))

            # VOLTAGE
            channel_widget.voltageDisp_label = QLabel("Actual Voltage")
            channel_widget.voltageDisp_label.setFont(QFont(shell_font, pointSize=8))
            channel_widget.voltageDisp = QLabel("00.00 V")
            channel_widget.voltageDisp.setAlignment(Qt.AlignRight)
            channel_widget.voltageDisp.setFont(QFont(shell_font, pointSize=24))
            channel_widget.voltageDisp.setStyleSheet('color: blue')

            channel_widget.voltageSet_label = QLabel("Set Voltage")
            channel_widget.voltageSet_label.setFont(QFont(shell_font, pointSize=8))
            channel_widget.voltageSet = QCustomUnscrollableSpinBox()
            channel_widget.voltageSet.setRange(0, 30)
            channel_widget.voltageSet.setDecimals(3)
            channel_widget.voltageSet.setSingleStep(1)
            channel_widget.voltageSet.setKeyboardTracking(False)
            channel_widget.voltageSet.setFont(QFont(shell_font, pointSize=16))
            channel_widget.voltageSet.setAlignment(Qt.AlignRight)

            channel_widget.voltageMax_label = QLabel("Max Voltage")
            channel_widget.voltageMax_label.setFont(QFont(shell_font, pointSize=8))
            channel_widget.voltageMax = QCustomUnscrollableSpinBox()
            channel_widget.voltageMax.setRange(0, 30)
            channel_widget.voltageMax.setDecimals(3)
            channel_widget.voltageMax.setSingleStep(1)
            channel_widget.voltageMax.setKeyboardTracking(False)
            channel_widget.voltageMax.setFont(QFont(shell_font, pointSize=16))
            channel_widget.voltageMax.setAlignment(Qt.AlignRight)

            # CURRENT
            channel_widget.currentDisp_label = QLabel("Actual Current")
            channel_widget.currentDisp_label.setFont(QFont(shell_font, pointSize=8))
            channel_widget.currentDisp = QLabel("00.00 A")
            channel_widget.currentDisp.setAlignment(Qt.AlignRight)
            channel_widget.currentDisp.setFont(QFont(shell_font, pointSize=24))
            channel_widget.currentDisp.setStyleSheet('color: blue')

            channel_widget.currentSet_label = QLabel("Set Current")
            channel_widget.currentSet_label.setFont(QFont(shell_font, pointSize=8))
            channel_widget.currentSet = QCustomUnscrollableSpinBox()
            channel_widget.currentSet.setRange(0, 30)
            channel_widget.currentSet.setDecimals(3)
            channel_widget.currentSet.setSingleStep(1)
            channel_widget.currentSet.setKeyboardTracking(False)
            channel_widget.currentSet.setFont(QFont(shell_font, pointSize=16))
            channel_widget.currentSet.setAlignment(Qt.AlignRight)

            channel_widget.currentMax_label = QLabel("Max Current")
            channel_widget.currentMax_label.setFont(QFont(shell_font, pointSize=8))
            channel_widget.currentMax = QCustomUnscrollableSpinBox()
            channel_widget.currentMax.setRange(0, 30)
            channel_widget.currentMax.setDecimals(3)
            channel_widget.currentMax.setSingleStep(1)
            channel_widget.currentMax.setKeyboardTracking(False)
            channel_widget.currentMax.setFont(QFont(shell_font, pointSize=16))
            channel_widget.currentMax.setAlignment(Qt.AlignRight)

            # lay out channel
            channel_widget_layout.addWidget(channel_title,                          0, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageDisp_label,       1, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageDisp,             2, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentDisp_label,       1, 1, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentDisp,             2, 1, 1, 1)

            channel_widget_layout.addWidget(channel_widget.voltageSet_label,        3, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageSet,              4, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentSet_label,        3, 1, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentSet,              4, 1, 1, 1)

            channel_widget_layout.addWidget(channel_widget.voltageMax_label,        5, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageMax,              6, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentMax_label,        5, 1, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentMax,              6, 1, 1, 1)

            channel_widget_layout.addWidget(channel_widget.toggleswitch,            7, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.lockswitch,              7, 1, 1, 1)

            # add channel to holder
            self.channels.append(channel_widget)
            layout.addWidget(channel_widget, 1 + i // 2, i % 2, 1, 1)

    def _lock(self, channel_num, status):
        channel_widget = self.channels[channel_num]
        channel_widget.voltage.setEnabled(status)
        channel_widget.toggleswitch.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(powersupply_gui)
