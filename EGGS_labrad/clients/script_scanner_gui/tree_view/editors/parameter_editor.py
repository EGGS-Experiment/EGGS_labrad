from os import path
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QAbstractItemDelegate, QDataWidgetMapper

basepath = path.dirname(__file__)
path = path.join(basepath, "..", "..", "Views", "ParameterEditor.ui")
paramBase, paramForm = uic.loadUiType(path)


class parameter_delegate(QAbstractItemDelegate):
    """
    Todo: document
    """

    def __init__(self, parent):
        super(parameter_delegate, self).__init__()
        self.parent = parent
        self.parent.uiValue.editingFinished.connect(self.on_new_value)
        self.parent.uiMin.editingFinished.connect(self.on_new_min)
        self.parent.uiMax.editingFinished.connect(self.on_new_max)
        
    def setEditorData(self, editor, index):
        node = index.internalPointer()
        if editor == self.parent.uiName or editor == self.parent.uiCollection:
            editor.setText(node.data(index.column()))
        elif editor == self.parent.uiValue:             
            editor.setValue(node.data(index.column()))
        elif editor == self.parent.uiMin:
            editor.setValue(node.data(index.column()))
            self.parent.uiValue.setMinimum(node.data(index.column()))
        elif editor == self.parent.uiMax:
            editor.setValue(node.data(index.column()))
            self.parent.uiValue.setMaximum(node.data(index.column()))
        elif index.column() == 6:
            suffix = node.data(index.column())
            self.parent.uiValue.setSuffix(suffix)
            self.parent.uiMin.setSuffix(suffix)
            self.parent.uiMax.setSuffix(suffix)
    
    def on_new_value(self):
        self.commitData.emit(self.parent.uiValue)
    
    def on_new_min(self):
        self.commitData.emit(self.parent.uiMin)
    
    def on_new_max(self):
        self.commitData.emit(self.parent.uiMax)
    
    def setModelData(self, editor, model, index):
        if index.column() == 6:
            return
        elif isinstance(editor, QtWidgets.QLineEdit):
            value = editor.text()
        else:
            value = editor.value()
        model.setData(index, value)


class ParameterEditor(paramBase, paramForm):
    """
    todo: document
    """
    
    max_columns = 10
    
    def __init__(self, parent=None):
        super(ParameterEditor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QDataWidgetMapper(self)
        self._dataMapper.setItemDelegate(parameter_delegate(self))
        self.connect_signals()
    
    def connect_signals(self):
        self.uiDecimals.valueChanged.connect(self.on_new_decimals)
    
    def on_new_decimals(self, decimals):
        for widget in [self.uiMin, self.uiMax, self.uiValue]:
            widget.setSingleStep(10**-decimals)
            widget.setDecimals(decimals)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiMin, 3)
        self._dataMapper.addMapping(self.uiMax, 4)
        self._dataMapper.addMapping(self.uiValue, 5)
        self._dataMapper.addMapping(QWidget(self), 6)
     
    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
