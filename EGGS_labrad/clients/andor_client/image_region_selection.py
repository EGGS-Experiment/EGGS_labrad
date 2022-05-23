from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGridLayout, QLabel, QSpinBox, QPushButton, QSizePolicy, QDialog

from twisted.internet.defer import inlineCallbacks


class image_region_selection_dialog(QDialog):
    def __init__(self, parent, server):
        super(image_region_selection_dialog, self).__init__(parent)
        self.server = server
        self.parent = parent
        self.setWindowTitle("Select Region")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setupLayout()

    def sizeHint(self):
        return QSize(300, 120)

    @inlineCallbacks
    def set_image_region(self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver):
        yield self.server.set_image_region(bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)

    @inlineCallbacks
    def setupLayout(self):
        self.hor_max, self.ver_max = yield self.server.get_detector_dimensions(None)
        self.hor_min, self.ver_min = [1, 1]
        cur_bin_hor, cur_bin_ver, cur_start_hor, cur_stop_hor, cur_start_ver, cur_stop_ver = yield self.server.getImageRegion(
            None)
        layout = QGridLayout(self)
        default_button = QPushButton("Default")
        start_label = QLabel("Start")
        stop_label = QLabel("Stop")
        bin_label = QLabel("Bin")
        hor_label = QLabel("Horizontal")
        ver_label = QLabel("Vertical")
        self.start_hor = QSpinBox()
        self.stop_hor = QSpinBox()
        self.bin_hor = QSpinBox()
        for button in [self.start_hor, self.stop_hor, self.bin_hor]:
            button.setRange(self.hor_min, self.hor_max)
        self.start_hor.setValue(cur_start_hor)
        self.stop_hor.setValue(cur_stop_hor)
        self.bin_hor.setValue(cur_bin_hor)
        self.start_ver = QSpinBox()
        self.stop_ver = QSpinBox()
        self.bin_ver = QSpinBox()
        for button in [self.start_ver, self.stop_ver, self.bin_ver]:
            button.setRange(self.ver_min, self.ver_max)
        self.start_ver.setValue(cur_start_ver)
        self.stop_ver.setValue(cur_stop_ver)
        self.bin_ver.setValue(cur_bin_ver)
        layout.addWidget(default_button,            0, 0)
        layout.addWidget(start_label,               0, 1)
        layout.addWidget(stop_label,                0, 2)
        layout.addWidget(bin_label,                 0, 3)
        layout.addWidget(hor_label,                 1, 0)
        layout.addWidget(self.start_hor,            1, 1)
        layout.addWidget(self.stop_hor,             1, 2)
        layout.addWidget(self.bin_hor,              1, 3)
        layout.addWidget(ver_label,                 2, 0)
        layout.addWidget(self.start_ver,            2, 1)
        layout.addWidget(self.stop_ver,             2, 2)
        layout.addWidget(self.bin_ver,              2, 3)
        submit_button = QPushButton("Submit")
        layout.addWidget(submit_button,             3, 0, 1, 2)
        cancel_button = QPushButton("Cancel")
        layout.addWidget(cancel_button,             3, 2, 1, 2)
        default_button.clicked.connect(self.on_default)
        submit_button.clicked.connect(self.on_submit)
        cancel_button.clicked.connect(self.on_cancel)

    def on_default(self, clicked):
        self.bin_hor.setValue(1)
        self.bin_ver.setValue(1)
        self.start_hor.setValue(self.hor_min)
        self.stop_hor.setValue(self.hor_max)
        self.start_ver.setValue(self.ver_min)
        self.stop_ver.setValue(self.ver_max)

    @inlineCallbacks
    def on_submit(self, clicked):
        bin_hor = self.bin_hor.value()
        bin_ver = self.bin_ver.value()
        start_hor = self.start_hor.value()
        stop_hor = self.stop_hor.value()
        start_ver = self.start_ver.value()
        stop_ver = self.stop_ver.value()
        yield self.do_submit(bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)

    @inlineCallbacks
    def do_submit(self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver):
        if self.parent.live_update_loop.running:
            yield self.parent.on_live_button(False)
            try:
                yield self.server.setImageRegion(None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
            except Exception as e:
                yield self.parent.on_live_button(True)
            else:
                yield self.parent.on_live_button(True)
                self.close()
        else:
            try:
                yield self.server.setImageRegion(None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
            except Exception as e:
                pass
            else:
                self.close()

    def on_cancel(self, clicked):
        self.close()
