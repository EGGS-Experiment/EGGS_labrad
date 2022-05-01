from os import path
from PyQt5 import uic
from PyQt5.QtWidgets import QDataWidgetMapper

basepath = path.dirname(__file__)
path = path.join(basepath, "..", "..", "Views", "SidebandSelectionEditor.ui")
base, form = uic.loadUiType(path)


class sideband_selection_editor(base, form):
    """
    Todo: document
    """

    def __init__(self, parent=None):
        super(sideband_selection_editor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QDataWidgetMapper(self)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiRadial1, 3)
        self._dataMapper.addMapping(self.uiRadial2, 4)
        self._dataMapper.addMapping(self.uiAxial, 5)
        self._dataMapper.addMapping(self.uiMicromotion, 6)

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
