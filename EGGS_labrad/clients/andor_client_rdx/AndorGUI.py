import pyqtgraph as pg

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QFrame, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox,
                             QPushButton, QCheckBox, QSizePolicy, QComboBox, QHBoxLayout)


from EGGS_labrad.clients import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox, QCustomUnscrollableSpinBox

_ANDOR_ALIGNMENT = (Qt.AlignRight | Qt.AlignVCenter)

# tmp remove
from andor_gui_sidebar import SidebarWidget
# tmp remove


class CameraDisplay(QWidget):
    """
    Main camera display window for Andor GUI.
    Intended for use as a sidebar display.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Camera Window")
        self._makeLayout()
        self._connectLayout()

    def _makeLayout(self):
        """
        todo: document
        :return:
        """
        # create master layout
        layout = QGridLayout(self)

        '''CREATE & CONFIGURE MAIN DISPLAY'''
        # create display widget for the camera image - a "symbol"
        # note: as a PlotItem, this is simply a representation of the actual image object
        self.display = pg.PlotItem()
        # todo: maybe need to create ROI here so we can initialize ImageView with it
        # create actual image object which holds and manages the images - a "referent"
        # note: as an ImageView, this can be considered as the actual image object
        self.image = pg.ImageView(view=self.display)

        # configure display
        self.display.showAxis('top')
        self.display.showAxis('bottom')
        self.display.showAxis('left')
        self.display.showAxis('right')
        self.display.setAspectLocked(True)
        self.display.vb.invertY(False)

        # configure image histogram (comes default when using ImageView)
        self.image.getHistogramWidget().setHistogramRange(0, 1000)


        '''CREATE DISPLAY OBJECTS'''
        # create crosshairs that center on a double-click
        self.crosshair_vline = pg.InfiniteLine(angle=90, movable=False)
        self.crosshair_hline = pg.InfiniteLine(angle=0, movable=False)
        # add crosshairs to display
        self.display.addItem(self.crosshair_vline, ignoreBounds=True)
        self.display.addItem(self.crosshair_hline, ignoreBounds=True)

        # todo: create ROI object
        # todo: can add post-fatviewbox.addItem(roi)
        # todo: create horiz and vert hists
        # todo: maybe have smaller zoom-out like a minimap?


        '''CREATE DISPLAY HELPER'''
        # cursor readout
        cursor_coordinates_label = QLabel("Cursor")
        self.cursor_coordinates = QLabel('(x, y):')
        self.cursor_coordinates.setFont(QFont(SHELL_FONT, pointSize=12))
        self.cursor_coordinates.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        cursor_signal_label = QLabel("Counts")
        self.cursor_signal = QLabel('1000')
        self.cursor_signal.setFont(QFont(SHELL_FONT, pointSize=12))
        self.cursor_signal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # box up cursor readout widget
        cursor_readout_holder = QWidget(self)
        cursor_readout_widget_layout = QGridLayout(cursor_readout_holder)
        cursor_readout_widget_layout.addWidget(cursor_coordinates_label,    0, 0, 1, 1)
        cursor_readout_widget_layout.addWidget(self.cursor_coordinates,     1, 0, 1, 1)
        cursor_readout_widget_layout.addWidget(cursor_signal_label,         0, 1, 1, 1)
        cursor_readout_widget_layout.addWidget(self.cursor_signal,          1, 1, 1, 1)
        # enclose section in a QGroupBox
        cursor_readout_widget = QCustomGroupBox(cursor_readout_holder, "Cursor")


        # ROI statistics readout
        roi_mean_label = QLabel("Mean Counts")
        self.roi_mean = QLabel('0.')
        self.roi_mean.setFont(QFont(SHELL_FONT, pointSize=12))
        self.roi_mean.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        roi_stdev_label = QLabel("Std. Dev.")
        self.roi_stdev = QLabel('0.')
        self.roi_stdev.setFont(QFont(SHELL_FONT, pointSize=12))
        self.roi_stdev.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        roi_max_label = QLabel("Max Counts")
        self.roi_max = QLabel('0.')
        self.roi_max.setFont(QFont(SHELL_FONT, pointSize=12))
        self.roi_max.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        roi_total_label = QLabel("Total Counts")
        self.roi_total = QLabel('0.')
        self.roi_total.setFont(QFont(SHELL_FONT, pointSize=12))
        self.roi_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # box up roi readout widget
        roi_readout_holder = QWidget(self)
        roi_readout_widget_layout = QGridLayout(roi_readout_holder)
        roi_readout_widget_layout.addWidget(roi_mean_label,     0, 0, 1, 1)
        roi_readout_widget_layout.addWidget(self.roi_mean,      1, 0, 1, 1)
        roi_readout_widget_layout.addWidget(roi_stdev_label,    0, 1, 1, 1)
        roi_readout_widget_layout.addWidget(self.roi_stdev,     1, 1, 1, 1)
        roi_readout_widget_layout.addWidget(roi_max_label,      0, 2, 1, 1)
        roi_readout_widget_layout.addWidget(self.roi_max,       1, 2, 1, 1)
        roi_readout_widget_layout.addWidget(roi_total_label,    0, 3, 1, 1)
        roi_readout_widget_layout.addWidget(self.roi_total,     1, 3, 1, 1)
        # enclose section in a QGroupBox
        roi_readout_widget = QCustomGroupBox(roi_readout_holder, "Analysis ROI")

        # todo: ROIs don't inherently display - no need to worry about this
        # todo: use ROI.getArrayRegion to get a slice; take statistics on this


        # create display helper widget
        display_helper_holder = QWidget(self)
        display_helper_widget_layout = QGridLayout(display_helper_holder)
        # lay out section
        display_helper_widget_layout.addWidget(cursor_readout_widget,   0, 0, 1, 1)
        display_helper_widget_layout.addWidget(roi_readout_widget,      0, 1, 1, 1)
        # enclose section in a QGroupBox
        display_helper_widget = QCustomGroupBox(display_helper_holder, "DISPLAY STATUS")


        '''CREATE USER MAIN INTERFACE'''
        # user interface buttons
        self.start_button = TextChangingButton(("Stop Acquisition", "Start Acquisition"))
        self.record_button = TextChangingButton(("Stop Recording", "Start Recording"))

        # create user main interface widget
        main_interface_holder = QWidget(self)
        main_interface_widget_layout = QGridLayout(main_interface_holder)
        # lay out section
        main_interface_widget_layout.addWidget(self.start_button,   0, 0, 1, 1)
        main_interface_widget_layout.addWidget(self.record_button,  0, 1, 1, 1)
        # enclose section in a QGroupBox
        main_interface_widget = QCustomGroupBox(main_interface_holder, "CAMERA CONTROL")


        '''CREATE USER DISPLAY INTERFACE'''
        # display adjust buttons
        self.display_view_all_button = QPushButton("View All")
        self.display_auto_level_button = QPushButton("Auto Level")

        # todo: lay out

        # tmp remove - create sidebar widget
        self.sidebar = SidebarWidget(self)
        # tmp remove - create sidebar widegt


        '''lay out GUI elements'''
        layout.addWidget(main_interface_widget,         0, 0, 1, 6)
        layout.addWidget(self.image,                    1, 0, 1, 6)
        layout.addWidget(display_helper_widget,         2, 0, 1, 6)
        layout.addWidget(self.sidebar,                  0, 6, 3, 1)


    def _connectLayout(self):
        # mouse-based events
        self.display.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.display.scene().sigMouseMoved.connect(self.mouse_moved)

        # todo: fix autorange and autolevels
        # self.display_auto_level_button.clicked.connect(lambda checked: self.image.autoLevels())
        # self.display_view_all_button.clicked.connect(lambda checked: self.image.autoRange())


    """
    SLOTS
    """
    def mouse_clicked(self, event):
        """
        Draw crosshairs at the position of a double click.
        Arguments:
            event {QMouseEvent}: the mouse click event.
        """
        # convert scene coordinates to item (i.e. display widget) coordinates
        # note: mouse click events always come as scene coordinates
        # todo: maybe convert first via display.mapFromScene(pos_scene) in case pos_scene becomes different?
        pos_disp = self.display.mapFromScene(event.pos())

        # ensure event is double click and is within display bounds
        if (event.double()) and (self.display.sceneBoundingRect().contains(pos_disp)):
            # convert display coordinates to view coordinates
            new_pos_disp = self.display.vb.mapToView(pos_disp)

            # draw crosshairs at new position
            self.crosshair_vline.setPos(new_pos_disp.x())
            self.crosshair_hline.setPos(new_pos_disp.y())

    def mouse_moved(self, pos_scene):
        """
        Display the coordinates at the mouse location.
        Arguments:
            pos {QPoint}: the mouse position on the Andor display.
        """
        # convert scene coordinates to viewbox coordinates
        # todo: maybe convert first via display.mapFromScene(pos_scene) in case pos_scene becomes different?
        pos_view = self.display.mapToView(pos_scene)
        self.cursor_coordinates.setText("({:.4g},\t{:.4g})".format(pos_view.x(), pos_view.y()))

        # todo: check if coords are in valid range
        # todo: get counts at that position


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(CameraDisplay)
