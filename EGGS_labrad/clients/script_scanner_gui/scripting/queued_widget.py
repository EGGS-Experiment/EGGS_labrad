"""
Shows all queued experiments.
"""
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSignalMapper, QSize, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy, QAbstractItemView,\
    QHeaderView, QTableWidget, QGridLayout, QPushButton


class queued_widget(QWidget):
    def __init__(self, reactor, ident, name, font=None, parent=None):
        super(queued_widget, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.ident = ident
        self.name = name
        self.font = QFont(self.font().family(), pointSize=10)
        if self.font is None:
            self.font = QFont()
        self.setup_layout()

    def setup_layout(self):
        layout = QHBoxLayout(self)
        self.id_label = QLabel('{0}'.format(self.ident))
        self.id_label.setFont(self.font)
        self.id_label.setMinimumWidth(30)
        self.id_label.setMinimumHeight(15)
        self.id_label.setAlignment(Qt.AlignCenter)
        self.id_label.setSizePolicy(QSizePolicy.Fixed,
                                    QSizePolicy.Fixed)
        self.name_label = QLabel(self.name)
        self.name_label.setFont(self.font)
        self.name_label.setAlignment(Qt.AlignLeft)
        self.name_label.setSizePolicy(QSizePolicy.MinimumExpanding,
                                      QSizePolicy.Fixed)
        self.name_label.setMinimumWidth(150)
        self.name_label.setMinimumHeight(15)
        self.cancel_button = fixed_width_button("Cancel", (75, 23))
        layout.addWidget(self.id_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.cancel_button)

    def closeEvent(self, x):
        self.reactor.stop()


class queued_list(QTableWidget):

    on_cancel = pyqtSignal(int)

    def __init__(self, reactor, font=None, parent=None):
        super(queued_list, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QFont('MS Shell Dlg 2', pointSize=12)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setupLayout()
        self.d = {}  # stores identification: corresponding widget
        self.mapper = QSignalMapper()
        self.mapper.mapped.connect(self.on_user_cancel)

    def on_user_cancel(self, ident):
        self.on_cancel.emit(ident)

    def setupLayout(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setColumnCount(1)
        self.setRowCount(1)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)

    def add(self, ident, name, order):
        # make the widget
        ident = int(ident)
        order = int(order)
        widget = queued_widget(self.reactor, parent=self.parent,
                               ident=ident, name=name)
        self.mapper.setMapping(widget.cancel_button, ident)
        widget.cancel_button.pressed.connect(self.mapper.map)
        self.d[ident] = widget
        # insert it
        self.insertRow(order)
        self.setCellWidget(order, 0, widget)
        # adjust size
        self.resizeColumnsToContents()

    def cancel_all(self):
        for ident in self.d.keys():
            self.on_cancel.emit(ident)

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

    def closeEvent(self, x):
        self.reactor.stop()


class queued_combined(QWidget):
    def __init__(self, reactor, font=None, parent=None):
        super(queued_combined, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QFont('MS Shell Dlg 2', pointSize=12)
        self.setupLayout()
        self.connect_layout()

    def clear_all(self):
        self.ql.clear()

    def setupLayout(self):
        layout = QGridLayout(self)
        title = QLabel("Queued", font=self.font)
        title.setAlignment(Qt.AlignLeft)
        self.ql = queued_list(self.reactor, self.parent)
        self.cancel_all = QPushButton("Cancel All")
        layout.addWidget(title,                     0, 0, 1, 2)
        layout.addWidget(self.cancel_all,           0, 2, 1, 1)
        layout.addWidget(self.ql,                   1, 0, 3, 3)

    def connect_layout(self):
        self.cancel_all.pressed.connect(self.ql.cancel_all)

    def add(self, ident, name, order):
        self.ql.add(ident, name, order)

    def remove(self, ident):
        self.ql.remove(ident)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(queued_combined)
