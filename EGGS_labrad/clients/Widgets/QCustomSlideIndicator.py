from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QFont


class QCustomSlideIndicator(QWidget):
    """
    A slide indicator that shows a value.
    """

    def __init__(self, limits, horizontal=True):
        super(QCustomSlideIndicator, self).__init__()
        self.setWindowTitle('Slide Indicator')
        self.setRails(limits)
        self.value = None
        if horizontal:
            self.setGeometry(2000, 200, 200, 30)
        else:
            self.setGeometry(2000, 200, 30, 200)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawGrid(qp)
        self.drawPointer(qp)
        qp.end()

    def drawGrid(self, qp):
        height = self.height()
        width = self.width()
        pen = QPen(Qt.gray, 2, Qt.SolidLine)
        qp.setPen(pen)
        # draw base line
        qp.drawLine(0, height - 1, width, height - 1)
        qp.setFont(QFont('MS Shell Dlg 2', 7))
        # draw text
        qp.drawText(0, height - 10, str(1000 * self.minvalue))
        #qp.drawText(width / 2, height - 10, str((self.maxvalue + self.minvalue)/2))
        qp.drawText(width - 50, height - 10, str(1000 * self.maxvalue))
        # draw dashes
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([1, width / 8.1 - 1])
        #print([1, width / 8.1 - 1])
        qp.setPen(pen)
        qp.drawLine(0, height - 2, width, height - 2)
        qp.drawLine(0, height - 3, width, height - 3)

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
