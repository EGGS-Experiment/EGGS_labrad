from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTabWidget

# from tab_image import SidebarTabImage
# from tab_acquisition import SidebarTabAcquisition
from EGGS_labrad.clients.andor_client.andor_gui_sidebar.tab_image import SidebarTabImage
from EGGS_labrad.clients.andor_client.andor_gui_sidebar.tab_save import SidebarTabSave
from EGGS_labrad.clients.andor_client.andor_gui_sidebar.tab_acquisition import SidebarTabAcquisition


class SidebarWidget(QTabWidget):
    """
    Sidebar Tab Widget for Andor GUI.
    Constituent tabs should be separate modules and imported.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # configure QTabWidget
        self.setWindowTitle("Sidebar Widget")
        self.setTabPosition(QTabWidget.TabPosition.East)

        self._makeLayout()
        self._connectLayout()

    def _makeLayout(self):
        """
        Create GUI layout.
        """
        # create acquisition configuration tab
        self.acquisition_config = SidebarTabAcquisition(self)
        # create image configuration tab
        self.image_config = SidebarTabImage(self)
        # create save configuration tab
        self.save_config = SidebarTabImage(self)

        # lay out GUI elements
        self.addTab(self.acquisition_config, "Acquisition")
        self.addTab(self.image_config, "Image")
        self.addTab(self.save_config, "Save")


    def _connectLayout(self):
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SidebarWidget)
