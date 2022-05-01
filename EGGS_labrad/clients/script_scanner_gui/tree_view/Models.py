"""
todo: document
"""
from .Nodes import *
from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel, QSortFilterProxyModel, pyqtSignal

__all__ = ["ParametersTreeModel", "FilterModel"]


class ParametersTreeModel(QAbstractItemModel):
    """
    todo: document
    """

    filterRole = Qt.UserRole
    on_new_parameter = pyqtSignal(tuple, tuple)
    
    def __init__(self, root, parent=None):
        super(ParametersTreeModel, self).__init__(parent)
        self._rootNode = root
        
    def rowCount(self, parent):
        """
        Returns the count.
        """
        if not parent.isValid():
            return self._rootNode.childCount()
        else:
            return parent.internalPointer().childCount()

    def columnCount(self, parent):
        return 2
        
    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return node.data(index.column())
        
        if role == ParametersTreeModel.filterRole:
            return node.filter_text()

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid():
            node = index.internalPointer()
            if role == Qt.EditRole:
                node.setData(index.column(), value)
                textIndex = self.createIndex(index.row(), 1, index.internalPointer())
                self.dataChanged.emit(index, index)
                self.dataChanged.emit(textIndex, textIndex)
                if not isinstance(node, CollectionNode):
                    self.on_new_parameter.emit(node.path(), node.full_parameter())
                return True
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if section == 0:
                return "Collection"
            else:
                return "Value"

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, index):      
        '''
        returns the index of the parent of the node at the given index
        '''
        node = self.getNode(index)
        parentNode = node.parent()
        if parentNode == self._rootNode:
            return QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)
        
    def index(self, row, column, parent): 
        '''
        returns the index for the given parent, row and column
        '''
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def getNode(self, index):
        '''
        returns node of the given index
        '''
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node            
        return self._rootNode

    def insert_collection(self, name, parent_index=QModelIndex()):
        parentNode = self.getNode(parent_index)
        row_count = self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = CollectionNode(name, parentNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_parameter(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = ParameterNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def insert_event(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = EventNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def insert_scan(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = ScanNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_bool(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = BoolNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_string(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = StringNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_selection_simple(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SelectionSimpleNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_line_selection(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = LineSelectionNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index

    def insert_sideband_selection(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SidebandElectorNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_duration_bandwidth(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = DurationBandwidthNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def insert_spectrum_sensitivity(self, parameter_name, info, parent_index):
        collectionNode = self.getNode(parent_index)
        row_count =  self.rowCount(parent_index)
        self.beginInsertRows(parent_index, row_count, row_count)
        childNode = SpectrumSensitivityNode(parameter_name, info, collectionNode)
        self.endInsertRows()
        index = self.index(row_count, 0, parent_index)
        return index
    
    def set_parameter(self, index, info):
        node = index.internalPointer()
        node.set_full_info(info)
        #refresh all columns
        max_index= self.createIndex(index.row(), node.columns, index.internalPointer())
        self.dataChanged.emit(index, max_index)
        
    def clear_model(self):
        rows = self._rootNode.childCount()
        self.beginRemoveRows(QModelIndex(), 0, rows)
        self._rootNode.clear_data()
        self.endRemoveRows()


class FilterModel(QSortFilterProxyModel):
    """
    todo: document
    """

    def __init__(self, parent):
        super(FilterModel, self).__init__(parent)
        # filtering
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)  # look at all columns while filtering
        # sorting
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self._show_only = []

    def filterAcceptsRow(self, row, index):
        model_index = self.sourceModel().index(row, 0, index)
        filter_text = self.sourceModel().data(model_index, self.filterRole())
        contains_filter = self.filterRegExp().pattern() in filter_text
        in_show_only = self._is_in_show_only(filter_text)
        return contains_filter and in_show_only

    def _is_in_show_only(self, filter_text):
        if not len(self._show_only):
            return True
        for collection, parameter in self._show_only:
            if (collection + parameter) in filter_text:
                return True
        return False

    def filterAcceptsColumn(self, column, index):
        return True

    def show_only(self, show):
        self._show_only = show
        self.invalidateFilter()

    def show_all(self):
        self._show_only = []
        self.invalidateFilter()

    def shown(self):
        return self._show_only
