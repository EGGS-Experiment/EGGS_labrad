from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.ionization_laser_shutter_client.ionization_laser_shutter_gui import IonizationLaserShutterGUI
from EGGS_labrad.clients.utils import SHELL_FONT
from labrad.logging import setupLogging, _LoggerWriter
import sys

class IonizationLasersShuttersClient(GUIClient):

    name = 'Ionization Lasers Shutters Client'
    servers = {'labjack': 'LabJack Server'}

    def getgui(self):

        if self.gui is None:
            self.gui = IonizationLaserShutterGUI()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # find desired device
        self.port_name_377 = "DIO0"
        self.port_name_423 = "DIO2"
        device_handle = yield self.labjack.device_info()
        self.logger = setupLogging('labrad.client', sender=self)
        sys.stdout = _LoggerWriter(self.logger.info)

        if device_handle == -1:
            # get device list
            dev_list = yield self.labjack.device_list()
            # assume desired labjack is first in list
            yield self.labjack.device_select(dev_list[0])

    @inlineCallbacks
    def initData(self):
        status_377 = yield self.labjack.read_name(self.port_name_377)
        status_423 = yield self.labjack.read_name(self.port_name_423)
        self.gui.toggle_377.setChecked(bool(status_377))
        self.gui.toggle_423.setChecked(bool(status_423))

    def initGUI(self):
        self.gui.toggle_377.clicked.connect(lambda status: self.labjack.write_name(self.port_name_377, status))
        self.gui.toggle_423.clicked.connect(lambda status: self.labjack.write_name(self.port_name_423, status))
        self.gui.lockswitch.clicked.connect(lambda status: self.lock(status))

        # set lockswitch to locked
        self.gui.lockswitch.setChecked(False)
        self.gui.lockswitch.click()

    def lock(self, status):
        """
        Locks ionization laser shutter interface
        """
        self.gui.toggle_377.setEnabled(status)
        self.gui.toggle_423.setEnabled(status)



if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(IonizationLasersShuttersClient)
