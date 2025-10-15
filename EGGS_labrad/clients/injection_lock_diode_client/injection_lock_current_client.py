from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.injection_lock_diode_client.injection_lock_current_gui import InjectionLockCurrentGUI

class InjectionLockCurrentClient(GUIClient):

    name = 'Injection Lock Current Client'
    servers = {'current_controller': 'InjectionLockCurrentServer'}

    TOGGLEID = 4651988
    CURRENTID = 4651989
    OUTPUTID = 4651990

    def getgui(self):

        if self.gui is None:
            self.gui = InjectionLockCurrentGUI()
        return self.gui

    @inlineCallbacks
    def initClient(self):

        yield self.current_controller.signal__toggle_update(self.TOGGLEID)
        yield self.current_controller.addListener(listener=self.updateToggle, soure=self.TOGGLEID)
        yield self.current_controller.signal__current_update(self.CURRENTID)
        yield self.current_controller.addListener(listener=self.updateSetCurrent, soure=None, ID=self.CURRENTID)
        yield self.current_Controller.signal__output_update(self.OUTPUTID)
        yield self.current_controller.addListener(listener=self.updateOutput, source=None, ID=self.OUTPUTID)
        # set up recording variables
        self.c_record = self.cxn.context()
        self.recording = False

    @inlineCallbacks
    def initData(self):
        status = self.current_controller.toggle()
        current = self.current_controller.currentSet()
        max_current = self.current_controller.currentMax()

        self.gui.output_button.setValue(status)
        self.gui.set_current_spinbox.setValue(current)
        self.gui.max_current_spinbox.setChecked(max_current)

    def initGUI(self):
        self.gui.set_current_spinbox.valueChanged.connect(lambda current_mA: self.current_controller.currentSet(current_mA))
        self.gui.max_current_spinbox.valueChanged.connect(lambda max_current_ma: self.current_controller.currentMax(max_current_ma))
        self.gui.output_button.clicked(lambda status: self.current_controller.toggle(status))

        self.gui.lockswitch.clicked.connect(lambda status: self.lock(status))

    def lock(self, status):
        """
        Locks 729 injection lock diode interface
        """
        self.gui.set_current_spinbox.setEnabled(status)
        self.gui.max_current_spinbox.setEnabled(status)
        self.gui.output_button.setEnabled(status)

    def updateSetCurrent(self,c, current_mA):
        self.gui.set_current_spinbox.setValue(current_mA)

    def updateToggle(self,c, status):
        self.gui.output_button.clicked(status)

    def updateOutput(self, c, output):
        self.gui.label_diode_current.setText(f'{output[0]:.3f} mA')
        self.gui.label_diode_voltage.setText(f'{output[1]:.3f} V')

if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(InjectionLockCurrentClient)