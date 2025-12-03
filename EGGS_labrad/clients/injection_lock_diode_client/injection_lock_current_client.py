from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.injection_lock_diode_client.injection_lock_current_gui import InjectionLockCurrentGUI


class InjectionLockCurrentClient(GUIClient):
    """
    LabRAD client for the 729nm Injection Lock Diode Current controller (the AMO1 peter box).
    Essentially a straightforward AMO1 client.
    """

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
        yield self.controller.addListener(listener=self.updateToggle, source=None, ID=self.TOGGLEID)
        yield self.controller.signal__current_update(self.CURRENTID)
        yield self.controller.addListener(listener=self.updateSetCurrent, source=None, ID=self.CURRENTID)
        yield self.controller.signal__output_update(self.OUTPUTID)
        yield self.controller.addListener(listener=self.updateOutput, source=None, ID=self.OUTPUTID)
        yield self.controller.signal__max_current_update(self.MAXCURRENTID)
        yield self.controller.addListener(listener=self.updateMaxCurrent, soure=None, ID=self.MAXCURRENTID)

        # start polliing only if not already started
        poll_params = yield self.controller.polling()
        if not poll_params[0]:  yield self.controller.polling(True, 5.0)

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
        self.gui.label_diode_voltage.setText("{:>.3f}".format(outputs[0]))
        self.gui.label_diode_current.setText("{:>.3f}".format(outputs[1] * 1e3))

    def initGUI(self):
        self.gui.set_current_spinbox.textChanged.connect(lambda _: self.gui.set_current_spinbox.blockSignals(True))
        self.gui.set_current_spinbox.lineEdit().connect(lambda _box=self.gui.set_current_spinbox,
                                                        _device_func = self.controller.current_set:
                                                        self.update_val(None, _box, _device_func))
        self.gui.max_current_spinbox.textChanged.connect(lambda _: self.gui.max_current_spinbox.blockSignals(True))
        self.gui.max_current_spinbox.lineEdit().connect(lambda _box=self.gui.max_current_spinbox,
                                                        _device_func = self.controller.current_max:
                                                        self.update_val(None, _box, _device_func))
        self.gui.output_button.clicked.connect(lambda status: self.controller.toggle(status))
        self.gui.lockswitch.clicked.connect(lambda status: self.lock(status))

    def update_val(self,c, box, device_func):
        val = float(box.text())
        device_func(val)

    def lock(self, status):
        """
        Disables 729 injection lock diode interface.
        """
        self.gui.set_current_spinbox.setEnabled(status)
        self.gui.max_current_spinbox.setEnabled(status)
        self.gui.output_button.setEnabled(status)

    """
    SLOTS FOR LABRAD SIGNALS
    """
    def updateToggle(self, c, status):
        """
        Update status of the toggle button (whether controller is outputting a current)
        Args:
            c: labrad context
            status: indicates if controller has been turned on or off
        """
        if not self.gui.output_button.signalsBlocked():
            self.gui.output_button.blockSignals(True)
            self.gui.output_button.setChecked(status)
            self.gui.output_button.setAppearance(status)
            self.gui.output_button.blockSignals(False)

    def updateSetCurrent(self, c, msg):
        """
        Update the listed current outputted by the controller
        Args:
            c: labrad context
            msg: message containing what the set current has been changed to
        """
        _, current_mA = msg
        if not self.gui.set_current_spinbox.signalsBlocked():
            self.gui.set_current_spinbox.blockSignals(True)
            self.gui.set_current_spinbox.setValue(current_mA)
            self.gui.set_current_spinbox.blockSignals(False)

    def updateMaxCurrent(self, c, msg):
        """
        Update the listed max current of the controller
        Args:
            c: labrad context
            msg: message containing what the max current has been changed to
        """
        _, current_mA = msg
        if not self.gui.max_current_spinbox.signalsBlocked():
            self.gui.max_current_spinbox.blockSignals(True)
            self.gui.max_current_spinbox.setValue(current_mA)
            self.gui.max_current_spinbox.blockSignals(False)

    def updateOutput(self, c, outputs):
        """
        Update the listed actual output of the controller
        Args:
            c: labrad context
            outputs: voltage and current the controller is outputting
        """
        if not self.gui.output_button.signalsBlocked():
            self.gui.label_diode_voltage.blockSignals(True)
            self.gui.label_diode_voltage.setText("{:>.3f}".format(outputs[0]))
            self.gui.label_diode_current.setText("{:>.3f}".format(outputs[1] * 1e3))
            self.gui.label_diode_current.blockSignals(False)

if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(InjectionLockCurrentClient)
