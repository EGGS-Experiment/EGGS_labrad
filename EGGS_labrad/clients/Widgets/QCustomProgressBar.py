from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressBar


class QCustomProgressBar(QProgressBar):
    """
    A progress bar with functions to
    easily set colors and orientation.
    """

    def __init__(self, max=4000, orientation=Qt.Vertical, border_color="orange",
                 start_color="orange", end_color="red"):
        super(QCustomProgressBar, self).__init__()
        self.setTextVisible(False)
        self.__blockStyle = False
        self.setOrientation(orientation)
        self.setMaximum(max)
        self.setMeterColor(start_color, end_color)
        self.setMeterBorder(border_color)

    def setMeterColor(self, start_color="green", end_color="red"):
        if self.orientation() == Qt.Vertical:
            mode_val = "vertical"
            if self.__blockStyle:
                self.setStyleSheet("QProgressBar::chunk:{} {{background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 {}, stop: 1 {});margin-top: 2px; height: 10px;}}"
                                   .format(mode_val, end_color, end_color))
            else:
                self.setStyleSheet("QProgressBar::chunk:{} {{background-color: qlineargradient(x1: 1, y1: 0, x2: 1, y2: 1, stop: 0 {}, stop: 1 {});}}"
                                   .format(mode_val, end_color, start_color))
        else:
            mode_val = "horizontal"
            if self.__blockStyle:
                self.setStyleSheet("QProgressBar::chunk:{} {{background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 {}, stop: 1 {});margin-right: 2px; width: 10px;}}"
                                   .format(mode_val, end_color, end_color))
            else:
                self.setStyleSheet("QProgressBar::chunk:{} {{background-color: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 1, stop: 0 {}, stop: 1 {});}}"
                                   .format(mode_val, start_color, end_color))

    def setMeterBorder(self, color):
        self.setStyleSheet("{}QProgressBar {{width: 25px;border: 2px solid {}; border-radius: 8px; background: #FFFFFF;text-align: center;padding: 0px;}}"
                           .format(self.styleSheet(), color))


if __name__ == '__main__':
    from EGGS_labrad.clients import runGUI
    runGUI(QCustomProgressBar)
