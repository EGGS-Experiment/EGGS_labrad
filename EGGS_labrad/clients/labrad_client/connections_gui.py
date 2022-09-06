from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QDoubleSpinBox, QComboBox, QGridLayout, QTreeWidget, QMenu, QFileDialog, QTreeWidgetItem

from EGGS_labrad.clients.Widgets import TextChangingButton as _TextChangingButton, QClientMenuHeader


class ConnectionsGUI(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__()
        # general initialization
        self.setWindowTitle("LabRAD Connections")
        # specific initialization
        self.setColumnCount(10)
        self.setHeaderLabels([
            "ID", "Type", "Name",
            "Server Requests", "Server Responses",
            "Client Requests", "Client Responses",
            "Messages Sent", "Messages Received",
            "Close"
        ])
        # create

    def addDataset(self, dataset_ident):
        """
        Adds a dataset header.
        Arguments:
            dataset_ident   (dataset_location, dataset_name): a unique identifier for a dataset.
        """
        if dataset_ident in self.dataset_dict.keys():
            print('Error in tracelist.addDataset: Dataset already exists.')
            print('\tdataset_ident:', dataset_ident)
        else:
            # create dataset header
            ident_tmp = list(dataset_ident)
            dataset_item = QTreeWidgetItem(self, ident_tmp[::-1])
            dataset_item.setExpanded(True)
            # store dataset_ident within dataset_item
            dataset_item.setData(0, Qt.UserRole, dataset_ident)
            # store header in self.dataset_dict
            self.dataset_dict[dataset_ident] = dataset_item

    def removeDataset(self, dataset_ident):
        """
        Removes a dataset header and all child traces.
        Arguments:
            dataset_ident   (dataset_location, dataset_name): a unique identifier for a dataset.
        """
        if dataset_ident not in self.dataset_dict.keys():
            print("Error in tracelist.removeDataset: dataset doesn't exist.")
            print('\tdataset_ident:', dataset_ident)
        else:
            dataset_item = self.dataset_dict.pop(dataset_ident, None)
            dataset_item.takeChildren()
            # remove dataset item from QTreeWidget
            dataset_item_index = self.indexOfTopLevelItem(dataset_item)
            self.takeTopLevelItem(dataset_item_index)
            # remove from parent
            self.parent.remove_dataset(dataset_ident)

    def addTrace(self, artist_ident, color):
        """
        Adds a trace to the TraceListWidget.
        Arguments:
            artist_ident    (dataset_location, dataset_name, artist_name): a unique identifier for an artist.
            color           Qt.Color: the color to set the trace.
        """
        dataset_ident = artist_ident[:2]
        # get dataset
        try:
            dataset_item = self.dataset_dict[dataset_ident]
            # create artist_item
            artist_item = QTreeWidgetItem(dataset_item, [artist_ident[2]])
            artist_item.setData(0, Qt.UserRole, artist_ident)
            artist_item.setBackground(0, QColor(0, 0, 0))
            artist_item.setCheckState(0, Qt.Checked)
            artist_item.setFirstColumnSpanned(True)
            # set color of artist entry in tracelist
            if self.use_trace_color:
                artist_item.setForeground(0, color)
            else:
                artist_item.setForeground(0, QColor(255, 255, 255))
            # add artist_item to dataset_item and holding dictionary
            dataset_item.addChild(artist_item)
            self.trace_dict[artist_ident] = artist_item
            dataset_item.sortChildren(0, Qt.AscendingOrder)
        except KeyError:
            print("Error in tracelist.addTrace: parent dataset doesn't exist")
            print("\tdataset_ident:", dataset_ident)

    def removeTrace(self, artist_ident):
        """
        Removes a trace from the TraceListWidget.
        Arguments:
            artist_ident   (dataset_location, dataset_name, artist_name): a unique identifier for an artist.
        """
        # get objects
        dataset_ident = artist_ident[:2]
        dataset_item = self.dataset_dict[dataset_ident]
        artist_item = self.trace_dict[artist_ident]
        # remove child from dataset_item
        artist_index = dataset_item.indexOfChild(artist_item)
        dataset_item.takeChild(artist_index)
        # remove artist_item from parent graphwidget
        self.parent.remove_artist(artist_ident)
        # remove parent dataset if empty
        if dataset_item.childCount() == 0:
            self.removeDataset(dataset_ident)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(ConnectionsGUI)
