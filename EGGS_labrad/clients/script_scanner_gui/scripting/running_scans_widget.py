"""
Displays currently running experiments.
"""
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSignalMapper, QSize, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QLabel,\
    QAbstractItemView, QTableWidget, QHeaderView, QGridLayout

from .shared_widgets import fixed_width_button, progress_bar


class script_status_widget(QWidget):
    """
    todo: document
    """
    on_pause = pyqtSignal()
    on_continue = pyqtSignal()
    on_stop = pyqtSignal()

    def __init__(self, reactor, ident, name, font=None, parent=None):
        super(script_status_widget, self).__init__(parent)
        self.reactor = reactor
        self.ident = ident
        self.name = name
        self.parent = parent
        self.font = QFont(self.font().family(), pointSize=10)
        if self.font is None:
            self.font = QFont()
        self.setup_layout()
        self.connect_layout()
        self.finished = False

    def setup_layout(self):
        layout = QHBoxLayout(self)
        self.id_label = QLabel('{0}'.format(self.ident))
        self.id_label.setFont(self.font)
        self.id_label.setMinimumWidth(30)
        self.id_label.setMinimumHeight(15)
        self.id_label.setAlignment(Qt.AlignCenter)
        self.id_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.name_label = QLabel(self.name)
        self.name_label.setFont(self.font)
        self.name_label.setAlignment(Qt.AlignLeft)
        self.name_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.name_label.setMinimumWidth(150)
        self.name_label.setMinimumHeight(15)
        self.progress_bar = progress_bar(self.reactor, self.parent)
        self.pause_button = fixed_width_button("Pause", (75, 23))
        self.stop_button = fixed_width_button("Stop", (75, 23))
        layout.addWidget(self.id_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)

    def connect_layout(self):
        self.stop_button.pressed.connect(self.on_user_stop)
        self.pause_button.pressed.connect(self.on_user_pause)

    def on_user_pause(self):
        if self.pause_button.text() == 'Pause':
            self.on_pause.emit()
        else:
            self.on_continue.emit()

    def on_user_stop(self):
        self.on_stop.emit()

    def set_paused(self, is_paused):
        if is_paused:
            self.pause_button.setText('Continue')
        else:
            self.pause_button.setText('Pause')

    def set_status(self, status, percentage):
        self.progress_bar.set_status(status, percentage)

    def closeEvent(self, x):
        self.reactor.stop()


class running_scans_list(QTableWidget):
    on_pause = pyqtSignal(int, bool)
    on_stop = pyqtSignal(int)

    def __init__(self, reactor, font=None, parent=None):
        super(running_scans_list, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QFont('MS Shell Dlg 2', pointSize=12)
        self.setupLayout()
        self.d = {}
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.mapper_pause = QSignalMapper()
        self.mapper_pause.mapped.connect(self.emit_pause)
        self.mapper_continue = QSignalMapper()
        self.mapper_continue.mapped.connect(self.emit_continue)
        self.mapper_stop = QSignalMapper()
        self.mapper_stop.mapped.connect(self.on_stop.emit)

    def emit_pause(self, ident):
        self.on_pause.emit(ident, True)

    def emit_continue(self, ident):
        self.on_pause.emit(ident, False)

    def setupLayout(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setColumnCount(1)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)

    def add(self, ident, name):
        ident = int(ident)
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        widget = script_status_widget(self.reactor,
                                      parent=self.parent,
                                      ident=ident, name=name, font=self.font)
        # set up signal mapping
        self.mapper_continue.setMapping(widget, ident)
        widget.on_continue.connect(self.mapper_continue.map)
        self.mapper_stop.setMapping(widget, ident)
        widget.on_stop.connect(self.mapper_stop.map)
        self.mapper_pause.setMapping(widget, ident)
        widget.on_pause.connect(self.mapper_pause.map)
        # insert widget
        self.setCellWidget(row_count, 0, widget)
        self.resizeColumnsToContents()
        self.d[ident] = widget

    def set_status(self, ident, status, percentage):
        try:
            widget = self.d[ident]
        except KeyError:
            print("Error: trying to set status of experiment that's not there")
        else:
            widget.set_status(status, percentage)

    def set_paused(self, ident, is_paused):
        try:
            widget = self.d[ident]
        except KeyError:
            print("Error: trying pause experiment that's not there")
        else:
            widget.set_paused(is_paused)

    def remove(self, ident):
        widget = self.d[ident]
        for row in range(self.rowCount()):
            if self.cellWidget(row, 0) == widget:
                del self.d[ident]
                self.removeRow(row)

    def sizeHint(self):
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        height = 0
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        return QSize(width, height)

    def finish(self, ident):
        try:
            self.remove(ident)
        except KeyError:
            print("trying remove experiment {0} that's not there".format(ident))

    def closeEvent(self, x):
        self.reactor.stop()


class running_combined(QWidget):
    """
    Brings a title together with the list of running experiments.
    Basically does nothing new, just a convenience class.
    """

    def __init__(self, reactor, font=None, parent=None):
        super(running_combined, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QFont('MS Shell Dlg 2', pointSize=12)
        self.setupLayout()

    def clear_all(self):
        self.scans_list.clear()

    def setupLayout(self):
        layout = QGridLayout(self)
        title = QLabel("Running", font=self.font)
        title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        title.setAlignment(Qt.AlignLeft)
        self.scans_list = running_scans_list(self.reactor, self.parent)
        layout.addWidget(title,             0, 0, 1, 3)
        layout.addWidget(self.scans_list,   1, 0, 3, 3)

    def add(self, ident, name):
        self.scans_list.add(ident, name)

    def set_status(self, ident, status, percentage):
        self.scans_list.set_status(ident, status, percentage)

    def paused(self, ident, is_paused):
        self.scans_list.set_paused(ident, is_paused)

    def finish(self, ident):
        self.scans_list.finish(ident)

    def closeEvent(self, x):
        self.reactor.stop()
