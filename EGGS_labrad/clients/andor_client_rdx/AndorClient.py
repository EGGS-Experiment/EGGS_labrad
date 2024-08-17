import os
import numpy as np
from datetime import datetime
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient

from EGGS_labrad.config.andor_config import AndorConfig as config
from EGGS_labrad.clients.andor_client_rdx.AndorGUI import AndorGUI
from EGGS_labrad.clients.andor_client.image_region_selection import image_region_selection_dialog
# todo: document
# todo: single camera image mode
# todo: make cursor xy stop stuttering
# todo: add temp to acq setup

# todo: link signals to slots
# todo: data saving
# todo: ROI


class AndorClient(GUIClient):
    """
    A client for Andor iXon cameras.
    """

    name =      "Andor Client"
    servers =   {'cam': 'Andor Server', 'dv': 'Data Vault'}
    IMAGE_UPDATED_ID =          8649321
    MODE_UPDATED_ID =           8649322
    PARAMETER_UPDATED_ID =      8649323

    def getgui(self):
        if self.gui is None:
            self.gui = AndorGUI()

    @inlineCallbacks
    def initClient(self):
        """
        Connect to relevant signals (i.e. updates) from the server,
        and perform other necessary initializations.
        """
        # connect to signals
        yield self.cam.signal__image_updated(self.IMAGE_UPDATED_ID)
        yield self.cam.addListener(listener=self.updateImage, source=None, ID=self.IMAGE_UPDATED_ID)
        yield self.cam.signal__mode_updated(self.MODE_UPDATED_ID)
        yield self.cam.addListener(listener=self.updateMode, source=None, ID=self.MODE_UPDATED_ID)
        yield self.cam.signal__parameter_updated(self.PARAMETER_UPDATED_ID)
        yield self.cam.addListener(listener=self.updateParameter, source=None, ID=self.PARAMETER_UPDATED_ID)

        # create global flag to manage image acquisition status
        self.update_display =   False

        # todo: set up saving etc.
        # get attributes from config
        self.saved_data =       None
        self.save_images =      False

        # get save path
        for attribute_name in ('image_path', 'save_in_sub_dir', 'save_format', 'save_header'):
            try:
                attribute = getattr(config, attribute_name)
                setattr(self, attribute_name, attribute)
            except Exception as e:
                print("Warning: {:s} not found in config.".format(attribute_name))

    @inlineCallbacks
    def initData(self):
        """
        Get data from server and set up initial values for GUI.
        """
        # link GUI elements to corresponding signal from server
        # self.gui_elements = {
        #     'EE': self.gui.ionizer_ee,  'IE': self.gui.ionizer_ie,  'FL': self.gui.ionizer_fl,
        #     'VF': self.gui.ionizer_vf,  'HV': self.gui.detector_hv, 'NF': self.gui.detector_nf,
        #     'SA': self.gui.scan_sa,     'MI': self.gui.scan_mi,     'MF': self.gui.scan_mf
        # }

        # get core camera configuration/capabilities
        detector_dimensions =       yield self.cam.info_detector_dimensions()
        gain_min, gain_max =        yield self.cam.info_emccd_range()
        vertical_shift_params =     yield self.cam.info_vertical_shift()
        horizontal_shift_params =   yield self.cam.info_horizontal_shift()

        self.gui.display.setLimits(xMin=0, xMax=detector_dimensions[0], yMin=0, yMax=detector_dimensions[1])
        self.gui.sidebar.acquisition_config.emccd_gain.setRange(gain_min, gain_max)

        vshift_speed_vals = vertical_shift_params[0][1]
        self.gui.sidebar.acquisition_config.shift_speed.addItems(vshift_speed_vals)
        vshift_ampl_vals = vertical_shift_params[1][1]
        self.gui.sidebar.acquisition_config.clock_voltage.addItems(vshift_ampl_vals)

        hshift_speed_vals = horizontal_shift_params[0][1]
        self.gui.sidebar.acquisition_config.readout_rate.addItems(hshift_speed_vals)
        hshift_preamp_gain_vals = horizontal_shift_params[1][1]
        self.gui.sidebar.acquisition_config.preamplifier_gain.addItems(hshift_preamp_gain_vals)


        # get camera modes
        trigger_mode =          yield self.cam.mode_trigger(None)
        acquisition_mode =      yield self.cam.mode_acquisition(None)
        read_mode =             yield self.cam.mode_read(None)
        shutter_mode =          yield self.cam.mode_shutter(None)

        # trigger_mode_ind = self.gui.trigger_mode.findText(trigger_mode)
        # self.gui.trigger_mode.setCurrentIndex(trigger_mode_ind)
        #
        # acquisition_mode_ind = self.gui.acquisition_mode.findText(acquisition_mode)
        # self.gui.acquisition_mode.setCurrentIndex(acquisition_mode_ind)


        # get current hardware setup
        emccd_gain =            yield self.cam.setup_emccd_gain()
        exposure_time_s =       yield self.cam.setup_exposure_time(None)
        vshift_speed =          yield self.cam.setup_vertical_shift_speed(None)
        vshift_ampl =           yield self.cam.setup_vertical_shift_amplitude(None)
        hshift_speed =          yield self.cam.setup_horizontal_shift_speed(None)
        hshift_preamp_gain =    yield self.cam.setup_horizontal_shift_preamp_gain(None)

        self.gui.sidebar.acquisition_config.emccd_gain.setValue(emccd_gain)
        self.gui.sidebar.acquisition_config.exposure_time.setValue(exposure_time_s)
        self.gui.sidebar.acquisition_config.shift_speed.setCurrentIndex(vshift_speed)
        self.gui.sidebar.acquisition_config.clock_voltage.setCurrentIndex(vshift_ampl)
        self.gui.sidebar.acquisition_config.readout_rate.setCurrentIndex(hshift_speed)
        self.gui.sidebar.acquisition_config.preamplifier_gain.setCurrentIndex(hshift_preamp_gain)


        # get current image setup
        flip_h, flip_v =        yield self.cam.image_flip()
        rotate_state_txt =      yield self.cam.image_rotate(None)

        self.gui.sidebar.image_config.flip_horizontal.setChecked(flip_h)
        self.gui.sidebar.image_config.flip_vertical.setChecked(flip_v)

        # find and set appropriate index for rotation since
        # the rotation function communicates via text (rather than index)
        index_rotate = self.gui.sidebar.image_config.rotation.findText(rotate_state_txt)
        self.gui.sidebar.image_config.rotation.setCurrentIndex(index_rotate)


    def initGUI(self):
        """
        Connect signals (i.e. events) to relevant slots (i.e. actions).
        """
        # camera hardware configuration buttons
        self.gui.sidebar.acquisition_config.exposure_time.valueChanged.connect(lambda value: self.set_exposure_time(value))
        self.gui.sidebar.acquisition_config.emccd_gain.valueChanged.connect(lambda value: self.set_emccd_gain(value))
        # todo: v/h shift
        # todo: image rotate/flip


        self.gui.start_button.toggled.connect(lambda status: self.start_acquisition(status))
        # self.gui.set_image_region_button.clicked.connect(self.on_set_image_region)
        # self.gui.save_images_button.stateChanged.connect(lambda state: setattr(self, 'save_images', state))


    """
    SLOTS
    """
    # self.gui.ionizer_ee.valueChanged.connect(lambda value: self.tempDisable('EE', self.rga.ionizer_electron_energy, int(value)))
    # self.gui.general_lockswitch.setChecked(False)
    # self.gui.general_lockswitch.toggled.connect(lambda status: self.general_lock(status))
    # self.general_lock(False)
    #
    # @inlineCallbacks
    # def tempDisable(self, element, func, *args):
    #     try:
    #         self.gui_elements[element].setEnabled(False)
    #     except Exception as e:
    #         self.log.error("Error when attempting to disable GUI element: {error}", error=e)
    #     yield func(*args)
    #
    # def updateValues(self, c, data):
    #     """
    #     Updates GUI when values are received from server.
    #     """
    #     param, value = data
    #     if param == 'SP':
    #         pass
    #     elif (param != 'status'):
    #         try:
    #             class_type = self.gui_elements[param].__class__.__name__
    #             if class_type == 'QDoubleSpinBox':
    #                 self.gui_elements[param].setValue(float(value))
    #             elif class_type == 'QComboBox':
    #                 self.gui_elements[param].setCurrentIndex(int(value))
    #         except Exception as e:
    #             self.log.error("Error updating values from signal: {error}", error=e)
    #             self.gui.buffer_readout.appendPlainText('{}: {}'.format(param, value))
    #         finally:
    #             try:
    #                 self.gui_elements[param].setEnabled(True)
    #             except KeyError:
    #                 pass

    @inlineCallbacks
    def set_exposure_time(self, exposure_time_s):
        acquisition_running = yield self.cam.acquisition_status()
        if not acquisition_running:
            yield self.cam.setup_exposure_time(exposure_time_s)

    @inlineCallbacks
    def set_emccd_gain(self, emccd_gain):
        acquisition_running = yield self.cam.acquisition_status()
        if not acquisition_running:
            yield self.cam.setup_emccd_gain(emccd_gain)

    @inlineCallbacks
    def set_vshift_speed(self, vshift_speed):
        acquisition_running = yield self.cam.acquisition_status()
        if not acquisition_running:
            yield self.cam.setup_vertical_shift_speed(vshift_speed)

    @inlineCallbacks
    def set_vshift_ampl(self, vshift_ampl):
        acquisition_running = yield self.cam.acquisition_status()
        if not acquisition_running:
            yield self.cam.setup_vertical_shift_speed(vshift_ampl)

    def updateMode(self, c, data):
        print('\tSignal received: {}'.format(data))
        # parameter_name, parameter_value = data
        # if parameter_name == "read":
        #     pass
        #     #self.gui.read_mode.setText(parameter_value)
        # elif parameter_name == "shutter":
        #     pass
        #     #self.gui.shutter_mode.setText(parameter_value)
        # elif parameter_name == "acquisition":
        #     self.gui.acquisition_mode.setText(parameter_value)
        # elif parameter_name == "trigger":
        #     self.gui.trigger_mode.setText(parameter_value)

    def updateParameter(self, c, temp):
        pass
        # todo


    """
    IMAGE UPDATING
    """
    @inlineCallbacks
    def start_acquisition(self, status):
        """
        Configures acquisition settings if server isn't already acquiring images,
        then allows received images to be updated to the display.
        """
        # set global update flag
        self.update_display = status

        # set image region
        self.binx, self.biny, self.startx, self.stopx, self.starty, self.stopy = yield self.cam.image_region_get()
        self.pixels_x = int((self.stopx - self.startx + 1) / self.binx)
        self.pixels_y = int((self.stopy - self.starty + 1) / self.biny)

        # prevent users from accessing camera configuration interface
        # during camera acquisition
        self.gui.sidebar.setEnabled(not status)

        if status:
            # configure camera for free-running video
            yield self.cam.mode_trigger('Internal')
            yield self.cam.mode_acquisition('Run till abort')
            yield self.cam.mode_shutter('Open')
            yield self.cam.acquisition_start()

            # tell camera to start polling
            yield self.cam.polling(True, 1.5)

        else:
            # stop acquisition and stop polling
            yield self.cam.acquisition_stop()
            yield self.cam.mode_shutter('Close')
            yield self.cam.polling(False)


    def updateImage(self, c, image_data):
        """
        Processes images received from the server.
        """
        if self.update_display:
            # process/reshape image shape
            image_data = np.reshape(image_data, (self.pixels_y, self.pixels_x))
            # update display
            self.gui.image.setImage(
                image_data.transpose(),
                pos=[self.startx, self.starty], scale=[self.binx, self.biny],
                autoRange=False, autoLevels=False, autoHistogramRange=False
            )

            # save image
            # if self.save_images: self.save_image(image_data)

    # todo: implement image region?
    def on_set_image_region(self, checked):
        # displays a non-modal dialog
        dialog = image_region_selection_dialog(self, self.cam)
        one = dialog.open()
        two = dialog.show()
        three = dialog.raise_()


    """
    IMAGE SAVING
    """
    def save_image(self, image_data):
        """
        todo: document
        Args:
            image_data:

        """
        # format data
        if not np.array_equal(image_data, self.saved_data):
            self.saved_data = image_data
            saved_data_in_int = self.saved_data.astype("int16")
            time_stamp = "-".join(self.datetime_to_str_list())

            # create path
            if self.save_in_sub_dir:
                path = self.check_save_path_exists()
                path = os.path.join(path, time_stamp)
            else:
                path = os.path.join(self.image_path, time_stamp)

            # create header
            header = ""
            if self.save_header:
                header = "shutter_time {:s}\nem_gain {:s}".format(self.gui.exposure.value(), self.gu.emccd.value())

            # save
            if self.save_format == "csv":
                np.savetxt(path + ".csv", saved_data_in_int, fmt='%i', delimiter=",", header=header)
            elif self.save_format == "bin":
                saved_data_in_int.tofile(path + ".dat")
            else:
                np.savetxt(path + ".tsv", saved_data_in_int, fmt='%i', header=header)


    """
    HELPER FUNCTIONS
    """
    def datetime_to_str_list(self):
        # todo: remove/consolidate
        dt = datetime.now()
        dt_str = [str(dt.year).rjust(4, "0"), str(dt.month).rjust(2, "0"), str(dt.day).rjust(2, "0"),
                  str(dt.hour).rjust(2, "0"),
                  str(dt.minute).rjust(2, "0"), str(dt.second).rjust(2, "0"),
                  str(int(dt.microsecond / 1000)).rjust(3, "0")]
        return dt_str

    def str_datetime_to_path(self, str_datetime):
        # todo: remove/consolidate
        year = str_datetime[0]
        month = str_datetime[1]
        day = year + "_" + month + "_" + str_datetime[2]
        return (year, month, day)

    def check_save_path_exists(self):
        # todo: remove/consolidate
        folders = self.str_datetime_to_path(self.datetime_to_str_list())
        path = self.image_path
        for sub_dir in folders:
            path = os.path.join(path, sub_dir)
            if not os.path.isdir(path):
                os.makedirs(path)
        return path


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(AndorClient)