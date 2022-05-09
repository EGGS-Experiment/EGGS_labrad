#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import numpy as np

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPen, QColor, QPainter, QPainterPath


class Wedge(object):

    def __init__(self, xcoord, ycoord, startingangle,
                 top_voltage=0.0, bottom_voltage=0.0):
        self.top_voltage = top_voltage
        self.bottom_voltage = bottom_voltage
        self.xcoord = xcoord
        self.ycoord = ycoord
        self.startingangle = startingangle
        self.change_color(0.0)

    def change_color(self, voltage):
        brightness = 150
        darkness = 255 - brightness

        R = int(brightness + voltage * darkness / 15.)
        G = int(brightness - abs(voltage * darkness / 15.))
        B = int(brightness - voltage * darkness / 15.)

        self.color = QColor(R, G, B, 127)


class ElectrodeIndicator(QWidget):

    def __init__(self, limits):
        super(ElectrodeIndicator, self).__init__()
        self.init_UI()
        self.minvalue = limits[0]
        self.maxvalue = limits[1]

    def init_UI(self):
        self.setGeometry(160, 160, 400, 400)

        quad1 = Wedge(None, None, 0.0)
        quad2 = Wedge(None, None, 90.0)
        quad3 = Wedge(None, None, 180.0)
        quad4 = Wedge(None, None, 270.0)
        self.quads = [quad1, quad2, quad3, quad4]
        self.setWindowTitle('Electrode Indicator')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.draw_wedges(qp)
        self.draw_values(qp)
        qp.end()

    def draw_wedges(self, qp):
        framewidth = self.frameGeometry().width()
        frameheight = self.frameGeometry().height()
        trapdim = .75 * min(framewidth, frameheight)
        center = QtCore.QPoint(framewidth / 2, frameheight / 2)

        xcoord = (framewidth - trapdim) / 2
        ycoord = (frameheight - trapdim) / 2

        pen = QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine)
        qp.setPen(pen)

        signs = [(1, -2), (-2, -2), (-2, 1), (1, 1)]

        for i in range(4):
            qp.drawText(center + QtCore.QPoint(signs[i][0] * trapdim / 8,
                                               signs[i][1] * trapdim / 8), str(round(self.quads[i].top_voltage, 4)))
            qp.drawText(center + QtCore.QPoint(signs[i][0] * trapdim / 8 + 20,
                                               signs[i][1] * trapdim / 8 + 20),
                        str(round(self.quads[i].bottom_voltage, 4)))

        pen = QPen(QtCore.Qt.gray, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)

        for quad in self.quads:
            qp.setBrush(quad.color)
            path = QPainterPath(center)
            path.arcTo(xcoord, ycoord,
                       trapdim, trapdim, quad.startingangle, 90.0)
            path.lineTo(center)
            qp.drawPath(path)

    def draw_values(self, qp):
        pen = QPen(QtCore.Qt.red, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)

    def update_octant(self, octant, value):

        if octant in [1, 2, 3, 4]:
            self.quads[octant - 1].top_voltage = value
            value2 = self.quads[octant - 1].bottom_voltage
            self.quads[octant - 1].change_color(np.mean([value, value2]))

        if octant in [5, 6, 7, 8]:
            self.quads[octant - 5].bottom_voltage = value
            value2 = self.quads[octant - 5].top_voltage
            self.quads[octant - 5].change_color(np.mean([value, value2]))
        self.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = ElectrodeIndicator([-5.0, 5.0])
    icon.show()
    app.exec_()
