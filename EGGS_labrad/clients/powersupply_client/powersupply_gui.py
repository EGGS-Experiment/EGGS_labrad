from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QComboBox

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomUnscrollableSpinBox, Lockswitch, QCustomGroupBox
# todo: max/ovp
# todo: use mode

class powersupply_gui(QFrame):
    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Power Supply Client")
        self.makeWidgets()

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QGridLayout(self)

        # title
        self.title = QLabel('Power Supply Client')
        self.title.setFont(QFont(shell_font, pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title, 0, 0, 1, 3)

        # create channel widgets
        self.channels = list()
        for i in range(3):

            # create and configure channel widget
            channel_widget = QFrame()
            channel_widget.setFrameStyle(0x0001 | 0x0030)
            channel_widget_layout = QGridLayout(channel_widget)

            # GENERAL
            channel_widget.toggleswitch = TextChangingButton(("On", "Off"))
            channel_widget.lockswitch = Lockswitch()
            channel_widget.lockswitch.clicked.connect(lambda status, _chan=i: self._lock(_chan, status))

            channel_widget.modeSelect = QComboBox()
            channel_widget.modeSelect.addItems(["Series", "Parallel"])

            # VOLTAGE
            channel_widget.voltageDisp_label = QLabel("Actual Voltage (V)")
            channel_widget.voltageDisp_label.setFont(QFont(shell_font, pointSize=10))
            channel_widget.voltageDisp = QLabel("00.00V")
            channel_widget.voltageDisp.setAlignment(Qt.AlignRight)
            channel_widget.voltageDisp.setFont(QFont(shell_font, pointSize=24))
            channel_widget.voltageDisp.setStyleSheet('color: blue')

            channel_widget.voltageSet_label = QLabel("Set Voltage (V)")
            channel_widget.voltageSet_label.setFont(QFont(shell_font, pointSize=10))
            channel_widget.voltageSet = QCustomUnscrollableSpinBox()
            channel_widget.voltageSet.setRange(0, 30)
            channel_widget.voltageSet.setDecimals(2)
            channel_widget.voltageSet.setSingleStep(1)
            channel_widget.voltageSet.setKeyboardTracking(False)
            channel_widget.voltageSet.setFont(QFont(shell_font, pointSize=16))
            channel_widget.voltageSet.setAlignment(Qt.AlignRight)

            channel_widget.voltageMax_label = QLabel("Max Voltage (V)")
            channel_widget.voltageMax_label.setFont(QFont(shell_font, pointSize=10))
            channel_widget.voltageMax = QCustomUnscrollableSpinBox()
            channel_widget.voltageMax.setRange(0, 30)
            channel_widget.voltageMax.setDecimals(2)
            channel_widget.voltageMax.setSingleStep(1)
            channel_widget.voltageMax.setKeyboardTracking(False)
            channel_widget.voltageMax.setFont(QFont(shell_font, pointSize=16))
            channel_widget.voltageMax.setAlignment(Qt.AlignRight)

            # CURRENT
            channel_widget.currentDisp_label = QLabel("Actual Current (A)")
            channel_widget.currentDisp_label.setFont(QFont(shell_font, pointSize=10))
            channel_widget.currentDisp = QLabel("0.00A")
            channel_widget.currentDisp.setAlignment(Qt.AlignRight)
            channel_widget.currentDisp.setFont(QFont(shell_font, pointSize=24))
            channel_widget.currentDisp.setStyleSheet('color: blue')

            channel_widget.currentSet_label = QLabel("Set Current (A)")
            channel_widget.currentSet_label.setFont(QFont(shell_font, pointSize=10))
            channel_widget.currentSet = QCustomUnscrollableSpinBox()
            channel_widget.currentSet.setRange(0, 30)
            channel_widget.currentSet.setDecimals(2)
            channel_widget.currentSet.setSingleStep(1)
            channel_widget.currentSet.setKeyboardTracking(False)
            channel_widget.currentSet.setFont(QFont(shell_font, pointSize=16))
            channel_widget.currentSet.setAlignment(Qt.AlignRight)

            channel_widget.currentMax_label = QLabel("Max Current (A)")
            channel_widget.currentMax_label.setFont(QFont(shell_font, pointSize=10))
            channel_widget.currentMax = QCustomUnscrollableSpinBox()
            channel_widget.currentMax.setRange(0, 30)
            channel_widget.currentMax.setDecimals(2)
            channel_widget.currentMax.setSingleStep(1)
            channel_widget.currentMax.setKeyboardTracking(False)
            channel_widget.currentMax.setFont(QFont(shell_font, pointSize=16))
            channel_widget.currentMax.setAlignment(Qt.AlignRight)

            # lay out channel
            channel_widget_layout.addWidget(channel_widget.voltageDisp_label,       0, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageDisp,             1, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentDisp_label,       0, 1, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentDisp,             1, 1, 1, 1)

            channel_widget_layout.addWidget(channel_widget.voltageSet_label,        2, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageSet,              3, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentSet_label,        2, 1, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentSet,              3, 1, 1, 1)

            channel_widget_layout.addWidget(channel_widget.voltageMax_label,        4, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.voltageMax,              5, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentMax_label,        4, 1, 1, 1)
            channel_widget_layout.addWidget(channel_widget.currentMax,              5, 1, 1, 1)

            channel_widget_layout.addWidget(channel_widget.toggleswitch,            6, 0, 1, 1)
            channel_widget_layout.addWidget(channel_widget.lockswitch,              6, 1, 1, 1)

            # add channel to holder
            self.channels.append(channel_widget)
            layout.addWidget(
                QCustomGroupBox(channel_widget, "Channel {:d}".format(i + 1)),
                #1 + i // 2, i % 2, 1, 1
                1, i, 1, 1
            )

    def _lock(self, channel_num, status):
        channel_widget = self.channels[channel_num]
        channel_widget.toggleswitch.setEnabled(status)
        channel_widget.voltageSet.setEnabled(status)
        channel_widget.currentSet.setEnabled(status)
        channel_widget.voltageMax.setEnabled(status)
        channel_widget.currentMax.setEnabled(status)
        channel_widget.modeSelect.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(powersupply_gui)
