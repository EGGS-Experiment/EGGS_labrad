import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QCheckBox, QSizePolicy, QComboBox, QHBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton

_ANDOR_ALIGNMENT = (Qt.AlignRight | Qt.AlignVCenter)
# todo: make dark mode
# todo: integrate region selection into tabwidget

# todo: draw bounds for image display
# todo: create tabbed config area
# todo: make save images a button
# todo: add separate "save single image" button

# todo: bottom qtabwidget for config stuff
# todo: tab: binning
# todo: tab: pixel shift/gain/timing
# todo: tab: acquisition/readout/triggering
# todo: tab: cooler/temp set/fan

# todo: rhs ROI qtabwidget with each tab as different roi
# todo: recalculate button
# todo: stdev, mean, max, total, SNR
# todo: rhs statistics


class AndorGUI(QWidget):
    """
    A GUI for Andor iXon cameras.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Andor Client")
        self._makeLayout()
        self._connectLayout()

    def _makeLayout(self):
        """
        todo: document
        :return:
        """
        layout = QGridLayout(self)
        shell_font = 'MS Shell Dlg 2'

        """
        Create GUI elements
        """
        # image display
        self.plt = pg.PlotItem()
        self.img_view = pg.ImageView(view=self.plt)
        # self.plt.scale(-1, -1)
        self.plt.showAxis('top')
        self.plt.hideAxis('bottom')
        self.plt.setAspectLocked(True)
        self.img_view.getHistogramWidget().setHistogramRange(0, 1000)

        # set up viewbox
        # note: not sure why this fixes the mousemoved problem (previously using self.plt)
        vb = self.plt.vb
        self.img = pg.ImageItem()
        vb.addItem(self.img)

        # image display information widget
        # pwButtons = QWidget()
        # pwButtons_layout = QHBoxLayout(pwButtons)
        # self.coords = QLabel('')
        # self.pw.scene().sigMouseMoved.connect(self.mouseMoved)
        display_helper_widget = QWidget()
        display_helper_widget_layout = QHBoxLayout(display_helper_widget)
        self.display_coordinates = QLabel('')
        self.display_view_all_button = QPushButton("View All")
        self.display_auto_level_button = QPushButton("Auto Level")
        display_helper_widget_layout.addWidget(self.display_coordinates)
        display_helper_widget_layout.addWidget(self.display_view_all_button)
        display_helper_widget_layout.addWidget(self.display_auto_level_button)

        # display
        self.start_button = TextChangingButton(("Start Acquisition", "Stop Acquisition"))
        self.set_image_region_button = QPushButton("Set Image Region")

        # image saving
        self.save_images_button = QCheckBox('Save Images')


        # read mode
        read_label = QLabel("Read Mode")
        read_label.setAlignment(_ANDOR_ALIGNMENT)
        self.read_mode = QComboBox()
        self.read_mode.setFont(QFont(shell_font, pointSize=12))
        self.read_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.read_mode.addItems(['Full Vertical Binning', 'Multi-Track',
                                 'Random-Track', 'Single-Track', 'Image'])

        # shutter mode
        shutter_label = QLabel("Shutter Mode")
        shutter_label.setAlignment(_ANDOR_ALIGNMENT)
        self.shutter_mode = QComboBox()
        self.shutter_mode.setFont(QFont(shell_font, pointSize=12))
        self.shutter_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.shutter_mode.addItems(['Open', 'Auto', 'Close'])

        # acquisition mode
        acquisition_label = QLabel("Acquisition Mode")
        acquisition_label.setAlignment(_ANDOR_ALIGNMENT)
        self.acquisition_mode = QComboBox()
        self.acquisition_mode.setFont(QFont(shell_font, pointSize=12))
        self.acquisition_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.acquisition_mode.addItems(['Single Scan', 'Accumulate', 'Kinetics', 'Fast Kinetics', 'Run till abort'])

        # trigger mode
        trigger_label = QLabel("Trigger Mode")
        trigger_label.setAlignment(_ANDOR_ALIGNMENT)
        self.trigger_mode = QComboBox()
        self.trigger_mode.setFont(QFont(shell_font, pointSize=12))
        self.trigger_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.trigger_mode.addItems(['Internal', 'External', 'External Start',
                                    'External Exposure', 'External FVB EM',
                                    'Software Trigger', 'External Charge Shifting'])

        # exposure
        exposure_label = QLabel("Exposure")
        exposure_label.setAlignment(_ANDOR_ALIGNMENT)
        self.exposure = QDoubleSpinBox()
        self.exposure.setDecimals(3)
        self.exposure.setSingleStep(0.001)
        self.exposure.setRange(0.0, 10000.0)
        self.exposure.setKeyboardTracking(False)
        self.exposure.setSuffix(' s')

        # gain
        emccd_label = QLabel("EMCCD Gain")
        emccd_label.setAlignment(_ANDOR_ALIGNMENT)
        self.emccd = QSpinBox()
        self.emccd.setSingleStep(1)
        self.emccd.setKeyboardTracking(False)

        # crosshairs for plotting
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plt.addItem(self.vLine, ignoreBounds=True)
        self.plt.addItem(self.hLine, ignoreBounds=True)


        """
        Lay out GUI elements
        """
        layout.addWidget(self.img_view,                     0, 0, 1, 6)
        layout.addWidget(display_helper_widget,             1, 0, 1, 6)
        layout.addWidget(exposure_label,                    2, 4)
        layout.addWidget(self.exposure,                     2, 5)

        layout.addWidget(self.start_button,                 2, 0)
        layout.addWidget(self.set_image_region_button,      3, 0)
        layout.addWidget(self.save_images_button,           4, 0)

        layout.addWidget(trigger_label,                     2, 2)
        layout.addWidget(self.trigger_mode,                 2, 3)
        layout.addWidget(acquisition_label,                 3, 2)
        layout.addWidget(self.acquisition_mode,             3, 3)
        layout.addWidget(emccd_label,                       3, 4)
        layout.addWidget(self.emccd,                        3, 5)

    def _connectLayout(self):
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.plt.scene().sigMouseMoved.connect(self.mouse_moved)

        # todo: fix autorange and autolevels
        # self.display_auto_level_button.clicked.connect(lambda checked: self.img_view.autoLevels())
        # self.display_view_all_button.clicked.connect(lambda checked: self.img_view.autoRange())


    """
    SLOTS
    """
    def mouse_clicked(self, event):
        """
        Draw crosshairs at the position of a double click.
        """
        try:
            # get coordinates of mouse on the image
            pos = self.plt.mapFromScene(event.pos())

            # only draw crosshairs if mouse click is within bounds
            if (self.plt.sceneBoundingRect().contains(pos)) and (event.double()):
                mousePoint = self.plt.vb.mapToView(pos)
                self.vLine.setPos(mousePoint.x())
                self.hLine.setPos(mousePoint.y())

        except Exception as e:
            pass

    def mouse_moved(self, pos):
        """
        Display the coordinates at the mouse location.
        """
        pnt = self.img.mapFromScene(pos)
        string = "({:.4g},\t{:.4g})".format(pnt.x(), pnt.y())
        self.display_coordinates.setText(string)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(AndorGUI)
