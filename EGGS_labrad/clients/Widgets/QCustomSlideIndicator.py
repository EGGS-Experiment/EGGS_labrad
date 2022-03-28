from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen


class QCustomSlideIndicator(QWidget):
    """
    A slide indicator that shows a value.
    """

    def __init__(self, limits, horizontal=True):
        super(QCustomSlideIndicator, self).__init__()
        self.setWindowTitle('Slide Indicator')
        # set class variables
        self.value = None
        self.minvalue = None
        self.maxvalue = None
        self.span = None
        # set rails
        self.setRails(limits)
        if horizontal:
            self.setGeometry(2000, 200, 200, 30)
        else:
            self.setGeometry(2000, 200, 30, 200)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawGrid(qp)
        self.drawPointer(qp)
        qp.end()

    def drawGrid(self, qp):
        qp.setPen(QPen(Qt.gray, 2, Qt.SolidLine))
        qp.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([1, self.width() / 8.1 - 1])
        #print([1, self.width() / 8.1 - 1])
        #qp.setPen(pen)
        qp.drawLine(0, self.height() - 2, self.width(), self.height() - 2)
        qp.drawLine(0, self.height() - 3, self.width(), self.height() - 3)

    def drawPointer(self, qp):
        qp.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        if self.value is not None:
            xpos = ((self.value - self.minvalue) / self.span) * self.width()
            qp.drawLine(xpos, self.height() - 15, xpos, self.height() - 2)

    def setRails(self, rails):
        self.minvalue, self.maxvalue = rails
        self.span = self.maxvalue - self.minvalue
        self.repaint()

    def updateSlider(self, value):
        if value > self.maxvalue:
            value = self.maxvalue
        elif value < self.minvalue:
            value = self.minvalue
        self.value = value
        self.repaint()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(QCustomSlideIndicator, limits=[-5.0, 5.0])
