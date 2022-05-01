from os import path
from PyQt5 import uic
from PyQt5.QtWidgets import QDataWidgetMapper

basepath = path.dirname(__file__)
path = path.join(basepath, "..", "..", "Views", "BooleanEditor.ui")
base, form = uic.loadUiType(path)


class BoolEditor(base, form):
    """
    Todo: document
    """

    def __init__(self, parent=None):
        super(BoolEditor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QDataWidgetMapper(self)
        self.connect_layout()
        
    def connect_layout(self):
        self.uiValue.clicked.connect(self.on_check)
    
    def on_check(self):
        self._dataMapper.itemDelegate().commitData.emit(self.uiValue)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiValue, 3)

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
