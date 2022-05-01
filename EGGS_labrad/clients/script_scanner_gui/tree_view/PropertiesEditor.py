from PyQt5 import uic
from .Nodes import SidebandElectorNode, DurationBandwidthNode, SpectrumSensitivityNode
from .Nodes import ParameterNode, ScanNode, BoolNode, StringNode, SelectionSimpleNode, LineSelectionNode, EventNode
from .editors import *

from os import path
basepath = path.dirname(__file__)
path = path.join(basepath, "..", "Views", "Editors.ui")
propBase, propForm = uic.loadUiType(path)


class PropertiesEditor(propBase, propForm):
    """
    todo: document
    """
    
    def __init__(self, parent = None):
        super(propBase, self).__init__(parent)
        self.setupUi(self)
        self._proxyModel = None
        # create editors
        self._parametersEditor = ParameterEditor(self)
        self._scanEditor = ScanEditor(self)
        self._boolEditor = BoolEditor(self)
        self._stringEditor = StringEditor(self)
        self._selectionSimpleEditor = SelectionSimpleEditor(self)
        self._lineSelectionEdtior = line_selection_editor(self)
        self._sideband_selection_editor = sideband_selection_editor(self)
        self._DurationBandwidthEditor = DurationBandwidthEditor(self)
        self._spectrum_sensitivity_editor = spectrum_sensitivity_editor(self)
        self._eventEditor = EventEditor(self)
        self._editors = [
            self._parametersEditor, self._scanEditor, self._stringEditor, self._boolEditor,
            self._selectionSimpleEditor, self._lineSelectionEdtior, self._sideband_selection_editor,
            self._DurationBandwidthEditor, self._spectrum_sensitivity_editor, self._eventEditor
        ]
        # add editors to layout
        self.layoutSpecs.addWidget(self._parametersEditor)
        # hide the edtiors
        for edit in self._editors:
            edit.setVisible(False)
               
    def setSelection(self, current, old):
        current = self._proxyModel.mapToSource(current)
        node = current.internalPointer()
        if isinstance(node, ParameterNode):
            self.show_only_editor(self._parametersEditor, current)
        elif isinstance(node, ScanNode):
            self.show_only_editor(self._scanEditor, current)
        elif isinstance(node, BoolNode):
            self.show_only_editor(self._boolEditor, current)
        elif isinstance(node, StringNode):
            self.show_only_editor(self._stringEditor, current)    
        elif isinstance(node, SelectionSimpleNode):
            self.show_only_editor(self._selectionSimpleEditor, current)    
        elif isinstance(node, LineSelectionNode):
            self.show_only_editor(self._lineSelectionEdtior, current)    
        elif isinstance(node, SidebandElectorNode):
            self.show_only_editor(self._sideband_selection_editor, current)
        elif isinstance(node, DurationBandwidthNode):
            self.show_only_editor(self._DurationBandwidthEditor, current)
        elif isinstance(node, SpectrumSensitivityNode):
            self.show_only_editor(self._spectrum_sensitivity_editor, current)
        elif isinstance(node, EventNode):
            self.show_only_editor(self._eventEditor, current)
        else:
            for edit in self._editors:
                edit.setVisible(False)
    
    def show_only_editor(self, only_editor, current_selection):
        for edit in self._editors:
            if only_editor == edit:
                only_editor.setVisible(True)
                only_editor.setSelection(current_selection)
            else:
                edit.setVisible(False) 
        
    def setModel(self, proxyModel):
        """
        Sets the model for all the editors.
        """
        self._proxyModel = proxyModel
        for edit in self._editors:
            edit.setModel(proxyModel)
