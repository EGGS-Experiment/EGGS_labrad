from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressBar


class QScrollBox(QProgressBar):
    """
    A holder widget that holds multiple of the
    same sub-widget and allows scrolling.
    """

    # wavemeter channels
    qBox_wm = QGroupBox('Wavemeter Channels')
    qBox_wm_layout = QGridLayout(qBox_wm)
    # wavemeter buttons
    self.startSwitch = TextChangingButton('Wavemeter')
    self.startSwitch.setMaximumHeight(50)
    self.lockSwitch = TextChangingButton('Locking')
    self.lockSwitch.setMaximumHeight(50)
    qBox_wm_layout.addWidget(self.startSwitch, 0, 0)
    qBox_wm_layout.addWidget(self.lockSwitch, 0, 1)
    # holder for wavemeter channels
    wm_scroll = QScrollArea()
    wm_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    wmChan_widget = QWidget()
    wmChan_layout = QGridLayout(wmChan_widget)
    qBox_wm_layout.addWidget(wm_scroll, 1, 0, 1, 2)


if __name__ == '__main__':
    from EGGS_labrad.clients import runGUI
    runGUI(QScrollBox)
