import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QCheckBox, QLineEdit, QSizePolicy

_ANDOR_ALIGNMENT = (Qt.AlignRight | Qt.AlignVCenter)
# todo: make dark mode
# todo: integrate region selection into tabwidget

# todo: make trigger mode and acquisition mode interface qcombobox
# todo: move "s" from expsure outside of it
# todo: add v and h bins

# todo: make save images a button
# todo: add separate "save single image" button
# todo: background button
# todo: continuously autorange button

# todo: bottom qtabwidget for config stuff
# todo: tab: binning
# todo: tab: pixel shift/gain/timing
# todo: tab: acquisition/readout/triggering
# todo: tab: cooler/temp set/fan

# todo: rhs ROI qtabwidget with each tab as different roi
# todo: recalculate button
# todo: live update button
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
        layout = QGridLayout(self)
        self.plt = pg.PlotItem()
        self.img_view = pg.ImageView(view=self.plt)
        self.plt.showAxis('top')
        self.plt.hideAxis('bottom')
        self.plt.setAspectLocked(True)
        self.img_view.getHistogramWidget().setHistogramRange(0, 1000)

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

        # display
        self.live_button = QPushButton("Acquisition Start")
        self.live_button.setCheckable(True)
        self.set_image_region_button = QPushButton("Set Image Region")
        self.save_images_button = QCheckBox('Save Images')
        self.view_all_button = QPushButton("View All")
        self.auto_levels_button = QPushButton("Auto Levels")

        # todo: read

        # todo: shutter

        # acquisition
        acquisition_label = QLabel("Acquisition Mode")
        acquisition_label.setAlignment(_ANDOR_ALIGNMENT)
        self.acquisition_mode = QLineEdit()
        self.acquisition_mode.setReadOnly(True)
        self.acquisition_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # todo: make qcombobox

        # trigger
        trigger_label = QLabel("Trigger Mode")
        trigger_label.setAlignment(_ANDOR_ALIGNMENT)
        self.trigger_mode = QLineEdit()
        self.trigger_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.trigger_mode.setReadOnly(True)
        # todo: make qcombobox

        # add lines for the cross
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plt.addItem(self.vLine, ignoreBounds=True)
        self.plt.addItem(self.hLine, ignoreBounds=True)

        # lay out
        layout.addWidget(self.img_view,                     0, 0, 1, 6)
        layout.addWidget(exposure_label,                    1, 4)
        layout.addWidget(self.exposure,                     1, 5)

        layout.addWidget(self.live_button,                  1, 0)
        layout.addWidget(self.set_image_region_button,      2, 0)
        layout.addWidget(self.save_images_button,           3, 0)

        layout.addWidget(trigger_label,                     1, 2)
        layout.addWidget(self.trigger_mode,                 1, 3)
        layout.addWidget(acquisition_label,                 2, 2)
        layout.addWidget(self.acquisition_mode,             2, 3)
        layout.addWidget(emccd_label,                       2, 4)
        layout.addWidget(self.emccd,                        2, 5)
        layout.addWidget(self.view_all_button,              1, 1)
        layout.addWidget(self.auto_levels_button,           2, 1)

    def _connectLayout(self):
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        # todo: fix autorange and tuoelves
        self.auto_levels_button.clicked.connect(lambda checked: self.img_view.autoLevels())
        self.view_all_button.clicked.connect(lambda checked: self.img_view.autoRange())


    # SLOTS
    def mouse_clicked(self, event):
        """
        Draws the cross at the position of a double click.
        """
        pos = event.pos()
        if self.plt.sceneBoundingRect().contains(pos) and event.double():
            # only on double clicks within bounds
            mousePoint = self.plt.vb.mapToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(AndorGUI)
