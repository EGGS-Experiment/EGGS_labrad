from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.injection_lock_diode_client.injection_lock_current_gui import InjectionLockCurrentGUI

class InjectionLockCurrentClient(GUIClient):

    name = 'Injection Lock Current Client'
    servers = {'controller': 'Injection Lock Current Server'}

    TOGGLEID = 1651988
    CURRENTID = 1651989
    OUTPUTID = 1651990
    MAXCURRENTID = 1651991

    def getgui(self):

        if self.gui is None:
            self.gui = InjectionLockCurrentGUI()
        return self.gui

    @inlineCallbacks
    def initClient(self):

        yield self.controller.signal__toggle_update(self.TOGGLEID)
        yield self.controller.addListener(listener=self.updateToggle, soure=self.TOGGLEID)
        yield self.controller.signal__current_update(self.CURRENTID)
        yield self.controller.addListener(listener=self.updateSetCurrent, soure=None, ID=self.CURRENTID)
        yield self.controller.signal__output_update(self.OUTPUTID)
        yield self.controller.addListener(listener=self.updateOutput, source=None, ID=self.OUTPUTID)
        yield self.controller.signal__max_current_update(self.MAXCURRENTID)
        yield self.controller.addListener(listener=self.updateMaxCurrent, soure=None, ID=self.MAXCURRENTID)

        # start polliing
        poll_params = yield self.controller.polling()
        # only start if polling not start
        if not poll_params[0]:
            yield self.controller.polling(True, 5.0)
        # set up recording variables
        self.c_record = self.cxn.context()
        self.recording = False
        self.max_current_mA = 100.

    @inlineCallbacks
    def initData(self):
        status = yield self.controller.toggle()
        current = yield self.controller.current_set()
        max_current = yield self.controller.current_max(self.max_current_mA)
        outputs = yield self.controller.outputs()

        self.gui.output_button.setChecked(status)
        self.gui.set_current_spinbox.setValue(current)
        self.gui.max_current_spinbox.setValue(max_current)

        self.gui.label_diode_voltage.setText(str(outputs[0]))
        self.gui.label_diode_current.setText(str(outputs[1]*1e3))

    def initGUI(self):
        self.gui.set_current_spinbox.valueChanged.connect(lambda current_mA: self.controller.current_set(current_mA))
        self.gui.max_current_spinbox.valueChanged.connect(lambda max_current_ma: self.controller.current_max(max_current_ma))
        self.gui.output_button.clicked.connect(lambda status: self.controller.toggle(status))

        self.gui.lockswitch.clicked.connect(lambda status: self.lock(status))

    def lock(self, status):
        """
        Locks 729 injection lock diode interface
        """
        self.gui.set_current_spinbox.setEnabled(status)
        self.gui.max_current_spinbox.setEnabled(status)
        self.gui.output_button.setEnabled(status)

    def updateSetCurrent(self,c, msg):
        _, current_mA = msg
        self.gui.set_current_spinbox.blockSignals(True)
        self.gui.set_current_spinbox.setValue(current_mA)
        self.gui.set_current_spinbox.blockSignals(False)

    def updateToggle(self,c, status):
        self.gui.output_button.blockSignals(True)
        self.gui.output_button.setChecked(status)
        self.gui.output_button.setAppearance(status)
        self.gui.output_button.blockSignals(False)

    def updateMaxCurrent(self,c, msg):
        _, current_mA = msg
        self.gui.max_current_spinbox.blockSignals(True)
        self.gui.max_current_spinbox.setValue(current_mA)
        self.gui.max_current_spinbox.blockSignals(False)

    def updateOutput(self, c, outputs):
        self.gui.label_diode_voltage.blockSignals(True)
        self.gui.label_diode_current.blockSignals(True)
        self.gui.label_diode_voltage.setText(str(outputs[0]))
        self.gui.label_diode_current.setText(str(outputs[1]*1e3))
        self.gui.label_diode_voltage.blockSignals(False)
        self.gui.label_diode_current.blockSignals(False)

if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(InjectionLockCurrentClient)