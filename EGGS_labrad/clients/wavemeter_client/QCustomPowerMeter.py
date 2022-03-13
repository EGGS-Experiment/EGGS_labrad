from PyQt5 import QtCore, QtWidgets
import sys


class MQProgressBar(QtWidgets.QProgressBar):

    def __init__(self):
        super(MQProgressBar, self).__init__()
        self.setTextVisible(False)
        self.__blockStyle = False
        self.setMaximum(4000.0)

    def setValue(self, integer):
        QtWidgets.QProgressBar.setValue(self, integer)

    def setMeterColor(self, start_color="green", end_color="red"):
        mode_val = "horizontal"
        if self.orientation() == QtCore.Qt.Vertical:
            mode_val = "vertical"
            if self.__blockStyle:
                self.setStyleSheet(
                    "QProgressBar::chunk:%s {background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 %s, stop: 1 %s);margin-top: 2px; height: 10px;}" % (
                    mode_val, end_color, end_color))

            else:
                self.setStyleSheet(
                    "QProgressBar::chunk:%s {background-color: qlineargradient(x1: 1, y1: 0, x2: 1, y2: 1, stop: 0 %s, stop: 1 %s);}" % (
                    mode_val, end_color, start_color))
        else:
            if self.__blockStyle:
                self.setStyleSheet(
                    "QProgressBar::chunk:%s {background: qlineargradient(x1: 0, y1: 0.5, x2: 1, y2: 0.5, stop: 0 %s, stop: 1 %s);margin-right: 2px; width: 10px;}" % (
                    mode_val, end_color, end_color))
            else:
                self.setStyleSheet(
                    "QProgressBar::chunk:%s {background-color: qlineargradient(x1: 0, y1: 1, x2: 1, y2: 1, stop: 0 %s, stop: 1 %s);}" % (
                    mode_val, start_color, end_color))

    def setBlockStyle(self, mode):
        self.__blockStyle = mode
        self.setMeterColor()

    def setMeterBorder(self, color):
        self.setStyleSheet(
            "%sQProgressBar {width: 25px;border: 2px solid %s; border-radius: 8px; background: #FFFFFF;text-align: center;padding: 0px;}" % (
            self.styleSheet(), color))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("plastique"))
    mypb = MQProgressBar()
    mypb.setOrientation(QtCore.Qt.Horizontal)
    mypb.setMeterColor("orange", "red")
    mypb.setMeterBorder("orange")
    mypb.setValue(3000.0)
    mypb.show()
    sys.exit(app.exec_())
