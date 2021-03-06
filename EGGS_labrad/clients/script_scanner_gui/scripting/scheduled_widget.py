"""
Shows all scheduled experiments.
"""
from PyQt5 import QtGui, QtCore, QtWidgets
from .shared_widgets import fixed_width_button


class scheduled_widget(QtWidgets.QWidget):
    """
    todo: document
    """

    def __init__(self, reactor, ident, name, duration, font=None, parent=None):
        super(scheduled_widget, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.ident = ident
        self.name = name
        self.duration = duration
        self.font = QtGui.QFont(self.font().family(), pointSize=10)
        if self.font is None:
            self.font = QtGui.QFont()
        self.setup_layout()

    def setup_layout(self):
        layout = QtWidgets.QHBoxLayout(self)
        self.id_label = QtWidgets.QLabel('{0}'.format(self.ident))
        self.id_label.setFont(self.font)
        self.id_label.setMinimumWidth(30)
        self.id_label.setMinimumHeight(15)
        self.id_label.setAlignment(QtCore.Qt.AlignCenter)
        self.id_label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.name_label = QtWidgets.QLabel(self.name)
        self.name_label.setFont(self.font)
        self.name_label.setAlignment(QtCore.Qt.AlignLeft)
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                      QtWidgets.QSizePolicy.Fixed)
        self.name_label.setMinimumWidth(150)
        self.name_label.setMinimumHeight(15)
        self.scheduled_duration = QtWidgets.QSpinBox()
        self.scheduled_duration.setMinimumHeight(20)
        self.scheduled_duration.setRange(1, 3600)
        self.scheduled_duration.setKeyboardTracking(False)
        self.scheduled_duration.setSuffix(' sec')
        self.scheduled_duration.setValue(self.duration)
        self.cancel_button = fixed_width_button("Cancel", (75, 23))
        layout.addWidget(self.id_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.scheduled_duration)
        layout.addWidget(self.cancel_button)

    def closeEvent(self, x):
        self.reactor.stop()


class scheduled_list(QtWidgets.QTableWidget):
    """
    todo: document
    """
    on_cancel = QtCore.pyqtSignal(int)
    on_new_duration = QtCore.pyqtSignal(int, float)

    def __init__(self, reactor, font=None, parent=None):
        super(scheduled_list, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2', pointSize=12)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setupLayout()
        self.d = {}  # stores identification: corresponding widget
        self.mapper_cancel = QtCore.QSignalMapper()
        self.mapper_cancel.mapped.connect(self.on_user_cancel)
        self.mapper_duration = QtCore.QSignalMapper()
        self.mapper_duration.mapped.connect(self.on_user_new_duration)

    def on_user_cancel(self, ident):
        self.on_cancel.emit(ident)

    def on_user_new_duration(self, ident):
        widget = self.d[ident]
        duration = widget.scheduled_duration.value()
        self.on_new_duration.emit(ident, duration)

    def setupLayout(self):
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setColumnCount(1)
        self.setShowGrid(False)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)

    def add(self, ident, name, duration):
        ident = int(ident)
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        widget = scheduled_widget(self.reactor, parent=self.parent,
                                  ident=ident, name=name, duration=duration)
        self.mapper_cancel.setMapping(widget.cancel_button, ident)
        widget.cancel_button.pressed.connect(self.mapper_cancel.map)
        self.mapper_duration.setMapping(widget.scheduled_duration, ident)
        widget.scheduled_duration.valueChanged.connect(self.mapper_duration.map)
        self.setCellWidget(row_count, 0, widget)
        self.resizeColumnsToContents()
        self.d[ident] = widget

    def cancel_all(self):
        for ident in self.d.keys():
            self.on_cancel.emit(ident)

    def remove(self, ident):
        widget = self.d[ident]
        for row in range(self.rowCount()):
            if self.cellWidget(row, 0) == widget:
                del self.d[ident]
                self.removeRow(row)

    def update_duration(self, ident, duration):
        widget = self.d[ident]
        for row in range(self.rowCount()):
            if self.cellWidget(row, 0) == widget:
                widget.scheduled_duration.blockSignals(True)
                widget.scheduled_duration.setValue(duration)
                widget.scheduled_duration.blockSignals(False)

    def sizeHint(self):
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        height = 0
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        return QtCore.QSize(width, height)

    def closeEvent(self, x):
        self.reactor.stop()


class scheduled_combined(QtWidgets.QWidget):
    """
    todo: document
    """

    def __init__(self, reactor, font=None, parent=None):
        super(scheduled_combined, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QtGui.QFont('MS Shell Dlg 2', pointSize=12)
        self.setupLayout()
        self.connect_layout()

    def clear_all(self):
        self.sl.clear()

    def add(self, ident, name, duration):
        self.sl.add(ident, name, duration)

    def remove(self, ident):
        self.sl.remove(ident)

    def change(self, ident, duration):
        self.sl.update_duration(ident, duration)

    def setupLayout(self):
        layout = QtWidgets.QGridLayout(self)
        title = QtWidgets.QLabel("Scheduled", font=self.font)
        title.setAlignment(QtCore.Qt.AlignLeft)
        self.sl = scheduled_list(self.reactor, self.parent)
        self.cancel_all = QtWidgets.QPushButton("Cancel All")
        layout.addWidget(title,             0, 0, 1, 2)
        layout.addWidget(self.cancel_all,   0, 2, 1, 1)
        layout.addWidget(self.sl,           1, 0, 3, 3)

    def connect_layout(self):
        self.cancel_all.pressed.connect(self.sl.cancel_all)

    def closeEvent(self, x):
        self.reactor.stop()
