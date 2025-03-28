import os
import numpy as np
from datetime import datetime
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient

from EGGS_labrad.config.andor_config import AndorConfig as config
from EGGS_labrad.clients.andor_client.AndorGUI import AndorGUI
from EGGS_labrad.clients.andor_client.image_region_selection import image_region_selection_dialog
# todo: document
# todo: single camera image mode
# todo: continual camera polling


class AndorClient(GUIClient):
    """
    A client for Andor iXon cameras.
    """

    name = "Andor Client"
    servers = {'cam': 'Andor Server', 'dv': 'Data Vault'}
    IMAGE_UPDATED_ID =          8649321
    MODE_UPDATED_ID =           8649322
    PARAMETER_UPDATED_ID =      8649323

    def getgui(self):
        if self.gui is None:
            self.gui = AndorGUI()

    @inlineCallbacks
    def initClient(self):
        # connect to signals
        yield self.cam.signal__image_updated(self.IMAGE_UPDATED_ID)
        yield self.cam.addListener(listener=self.updateImage, source=None, ID=self.IMAGE_UPDATED_ID)
        yield self.cam.signal__mode_updated(self.MODE_UPDATED_ID)
        yield self.cam.addListener(listener=self.updateMode, source=None, ID=self.MODE_UPDATED_ID)
        yield self.cam.signal__parameter_updated(self.PARAMETER_UPDATED_ID)
        yield self.cam.addListener(listener=self.updateParameter, source=None, ID=self.PARAMETER_UPDATED_ID)

        # get attributes from config
        self.saved_data =       None
        self.save_images =      False
        self.update_display =   False

        # get save path
        for attribute_name in ('image_path', 'save_in_sub_dir', 'save_format', 'save_header'):
            try:
                attribute = getattr(config, attribute_name)
                setattr(self, attribute_name, attribute)
            except Exception as e:
                print("Warning: {:s} not found in config.".format(attribute_name))

    @inlineCallbacks
    def initData(self):
        # get core camera configuration
        detector_dimensions =   yield self.cam.info_detector_dimensions()
        gain_min, gain_max =    yield self.cam.info_emccd_range()

        trigger_mode =          yield self.cam.mode_trigger(None)
        acquisition_mode =      yield self.cam.mode_acquisition(None)

        gain =                  yield self.cam.setup_emccd_gain()
        exposure =              yield self.cam.setup_exposure_time(None)

        # configure camera gui
        self.gui.plt.setLimits(xMin=0, xMax=detector_dimensions[0], yMin=0, yMax=detector_dimensions[1])
        self.gui.emccd.setRange(gain_min, gain_max)
        self.gui.emccd.setValue(gain)
        self.gui.exposure.setValue(exposure)

        trigger_mode_ind = self.gui.trigger_mode.findText(trigger_mode)
        self.gui.trigger_mode.setCurrentIndex(trigger_mode_ind)

        acquisition_mode_ind = self.gui.acquisition_mode.findText(acquisition_mode)
        self.gui.acquisition_mode.setCurrentIndex(acquisition_mode_ind)

    def initGUI(self):
        # camera configuration buttons
        self.gui.exposure.valueChanged.connect(lambda value: self.set_exposure_time(value))
        self.gui.emccd.valueChanged.connect(lambda gain: self.cam.setup_emccd_gain(gain))

        # self.gui.set_image_region_button.clicked.connect(self.on_set_image_region)

        self.gui.start_button.toggled.connect(lambda status: self.update_start(status))
        # self.gui.save_images_button.stateChanged.connect(lambda state: setattr(self, 'save_images', state))


    """
    SLOTS
    """
    # todo: implement or whatever
    def on_set_image_region(self, checked):
        # displays a non-modal dialog
        dialog = image_region_selection_dialog(self, self.cam)
        one = dialog.open()
        two = dialog.show()
        three = dialog.raise_()

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
    def update_start(self, status):
        """
        Configures acquisition settings if server isn't already acquiring images,
        then allows received images to be updated to the display.
        """
        self.update_display = status
        if status:
            # todo: lock all camera configuration widgets

            # set up acquisition
            yield self.cam.mode_trigger('Internal')
            yield self.cam.mode_acquisition('Run till abort')
            yield self.cam.mode_shutter('Open')
            yield self.cam.acquisition_start()

            # set image region
            self.binx, self.biny, self.startx, self.stopx, self.starty, self.stopy = yield self.cam.image_region_get()
            self.pixels_x = int((self.stopx - self.startx + 1) / self.binx)
            self.pixels_y = int((self.stopy - self.starty + 1) / self.biny)

            # tell camera to start polling
            yield self.cam.polling(True, 1.5)

        else:
            # todo: tell server to stop updating if it doesn't have any listeners
            yield self.cam.acquisition_stop()
            yield self.cam.mode_shutter('Close')
            yield self.cam.polling(False)

    def updateImage(self, c, image_data):
        """
        Processes images received from the server.
        """
        if self.update_display:
            # process & update image
            image_data = np.reshape(image_data, (self.pixels_y, self.pixels_x))
            self.gui.img_view.setImage(image_data.transpose(), autoRange=False, autoLevels=False,
                                       pos=[self.startx, self.starty], scale=[self.binx, self.biny], autoHistogramRange=False)

            # save image
            # if self.save_images: self.save_image(image_data)

    def save_image(self, image_data):
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

    # todo: make start display start acquisition if not already started, then allow updating to pg


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(AndorClient)
