import labrad
import numpy as np
import h5py as h5
import os
import csv
import time
import sys
import inspect
import logging
from artiq.language import scan
from artiq.language.core import TerminationRequested, kernel
from artiq.experiment import *
from artiq.coredevice.ad9910 import (
    RAM_DEST_POW, RAM_DEST_POWASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_CONT_BIDIR_RAMP, RAM_MODE_CONT_RAMPUP, RAM_MODE_RAMPUP,
    RAM_DEST_ASF, RAM_DEST_FTW, RAM_MODE_DIRECTSWITCH
)
from sipyco.pc_rpc import Client
from artiq.dashboard.drift_tracker import client_config as dt_config
from artiq.readout_analysis import readouts
from easydict import EasyDict as edict
from datetime import datetime
from bisect import bisect
from collections import OrderedDict as odict
from itertools import product
from operator import mul
from functools import partial
from HardwareConfiguration import dds_config

absolute_frequency_plots = [
    "CalibLine1", "CalibLine2", "Spectrum", "CalibRed", "CalibBlue"
]
logger = logging.getLogger(__name__)


class PulseSequence(EnvExperiment):
    is_ndim = False
    kernel_invariants = set()
    scan_params = odict()  # Not working as expected
    range_guess = dict()
    data = edict()
    run_after = dict()
    set_subsequence = dict()
    fixed_params = list()
    master_scans = list()

    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("pmt")
        self.setattr_device("linetrigger_ttl")
        self.setattr_device("camera_ttl")
        self.setattr_device("core_dma")
        self.setattr_device("mod397")
        self.camera = None
        self.multi_scannables = dict()
        self.rcg_tabs = dict()
        self.selected_scan = dict()
        self.master_scan_iterables = list()
        self.master_scan_names = list()
        self.update_scan_params(self.scan_params)
        if self.master_scans:
            for scan_descr in self.master_scans:
                scan_name = scan_descr[0]
                self.master_scan_names.append(scan_name)
                self.accessed_params.update({scan_name})
                if len(scan_descr) == 4:
                    scannable = scan.Scannable(default=scan.RangeScan(*scan_descr[1:]))
                elif len(scan_descr) == 5:
                    scannable = scan.Scannable(
                        default=scan.RangeScan(*scan_descr[1:-1]),
                        unit=scan_descr[-1]
                    )
                self.master_scan_iterables.append(
                    self.get_argument(
                        scan_name,
                        scannable,
                        group="Master Scans"
                    )
                )
        self.run_in_build()

        # Load all AD9910 and AD9912 DDS channels specified in device_db
        self.dds_names = list()
        self.dds_offsets = list()
        self.dds_dp_flags = list()
        self.dds_device_list = list()
        for key, val in self.get_device_db().items():
            if isinstance(val, dict) and "class" in val:
                if val["class"] == "AD9910" or val["class"] == "AD9912":
                    setattr(self, "dds_" + key, self.get_device(key))
                    self.dds_device_list.append(getattr(self, "dds_" + key))
                    try:
                        self.dds_offsets.append(float(dds_config[key].offset))
                        self.dds_dp_flags.append(float(dds_config[key].double_pass))
                        self.dds_names.append(key)
                    except KeyError:
                        continue
        self.dds_729 = self.get_device("729G")
        self.dds_729_SP = self.get_device("SP_729G")
        self.dds_729_SP_bichro = self.get_device("SP_729G_bichro")
        self.dds_7291 = self.get_device("729G")
        self.dds_729_SP1 = self.get_device("SP_729G")
        self.dds_729_SP_bichro1 = self.get_device("SP_729G_bichro")
        self.dds_729_SP_line1 = self.get_device("SP_729G")
        self.dds_729_SP_line2 = self.get_device("SP_729G_bichro")
        self.dds_729_SP_line1_bichro = self.get_device("SP_729L2")
        self.dds_729_SP_line2_bichro = self.get_device("SP_729L2_bichro")
        self.cpld_list = [self.get_device("urukul{}_cpld".format(i)) for i in range(3)]

        # Initialize variables used for ramping
        self.ramp_slope_duration = 0 * us
        self.ramp_wait_duration = 0 * us
        self.dds1_ramp_up_profile = 2
        self.dds1_ramp_down_profile = 3  # must differ by exactly one binary digit from ramp-up
        self.dds2_ramp_up_profile = 4
        self.dds2_ramp_down_profile = 5  # must differ by exactly one binary digit from ramp-up
        self.noise_profile = 6
        self.noise_waveform = [0.0]
        self.noise_n_steps = 500
        self.current_noise_index = 0

    def prepare(self):
        # Grab parametervault params:
        G = globals().copy()
        self.G = G
        cxn = labrad.connect()
        self.global_cxn = labrad.connect(
            dt_config.global_address,
            password=dt_config.global_password,
            tls_mode="off"
        )
        self.sd_tracker = self.global_cxn.sd_tracker_global
        p = cxn.parametervault
        collections = p.get_collections()
        D = dict()
        for collection in collections:
            d = dict()
            names = p.get_parameter_names(collection)
            for name in names:
                try:
                    param = p.get_parameter([collection, name])
                    try:
                        units = param.units
                        if units == "":
                            param = param[units]
                        else:
                            param = param[units] * G[units]
                    except AttributeError:
                        pass
                    except KeyError:
                        if (units == "dBm" or
                                units == "deg" or
                                units == ""):
                            param = param[units]
                    d[name] = param
                except:
                    # broken parameter
                    continue
            D[collection] = d
        for item in self.fixed_params:
            collection, param = item[0].split(".")
            D[collection].update({param: item[1]})
        self.p = edict(D)
        self.cxn = cxn

        # Grab cw parameters:
        # NOTE: Because parameters are grabbed in prepare stage,
        # loaded dds cw parameters may not be the most current.
        self.dds_list = list()
        self.freq_list = list()
        self.amp_list = list()
        self.att_list = list()
        self.state_list = list()

        for key, settings in self.p.dds_cw_parameters.items():
            self.dds_list.append(getattr(self, "dds_" + key))
            self.freq_list.append(float(settings[1][0]) * 1e6)
            self.amp_list.append(float(settings[1][1]))
            self.att_list.append(float(settings[1][3]))
            self.state_list.append(bool(float(settings[1][2])))

        # Try to make rcg/hist connections
        try:
            self.rcg = Client("::1", 3286, "rcg")
        except:
            self.rcg = None
        try:
            self.pmt_hist = Client("::1", 3287, "pmt_histogram")
        except:
            self.pmt_hist = None

        # Make scan object for repeating the experiment
        N = int(self.p.StateReadout.repeat_each_measurement)
        self.N = N

        # Call run_initially method of sequence
        self.run_initially()

        # Create datasets and setup readout
        self.x_label = dict()
        self.timestamp = dict()
        scan_specs = dict()
        self.set_dataset("time", [])
        for seq_name, scan_dict in self.multi_scannables.items():
            self.data[seq_name] = dict(x=[], y=[])
            if isinstance(scan_dict[self.selected_scan[seq_name]], scan.NoScan):
                self.rcg_tabs[seq_name][self.selected_scan[seq_name]] = "Current"
            if self.is_ndim:
                scan_specs[seq_name] = [len(scan) for scan in scan_dict.values()]
            else:
                scan_specs[seq_name] = [len(scan_dict[self.selected_scan[seq_name]])]
        self.rm = self.p.StateReadout.readout_mode
        self.set_dataset("raw_run_data", np.full(N, np.nan))

        self.camera_string_states = []
        if self.rm in ["pmt", "pmt_parity", "pmtMLE"]:
            self.use_camera = False
            self.n_ions = len(self.p.StateReadout.threshold_list)
            for seq_name, dims in scan_specs.items():
                if not self.is_ndim:
                    # Currently not supporting any default plotting for (n>1)-dim scans
                    for i in range(self.n_ions):
                        setattr(
                            self,
                            "{}-dark_ions:{}".format(seq_name, i),
                            np.full(dims, np.nan)
                        )
                    if self.rm == "pmt_parity":
                        setattr(self, seq_name + "-parity", np.full(dims, np.nan))
                    x_array = np.array(list(self.multi_scannables[seq_name][self.selected_scan[seq_name]]))
                    self.x_label[seq_name] = [self.selected_scan[seq_name]]
                    f = seq_name + "-" if len(self.scan_params) > 1 else ""
                    f += self.x_label[seq_name][0]
                    setattr(self, f, x_array)
                else:
                    raise NotImplementedError("Ndim scans with PMT not implemented yet")
                if self.rm != "pmtMLE":
                    dims.append(N)
                    self.set_dataset(
                        "{}-raw_data".format(seq_name),
                        np.full(dims, np.nan),
                        broadcast=True
                    )
                else:
                    M = int(self.p.StateReadout.pmt_readout_duration // 1e-5)
                    dims.append(M)
                    dims.append(N)
                    self.set_dataset("mledata", np.full(M, np.nan), broadcast=True)
                    self.set_dataset(
                        "{}-raw_data".format(seq_name),
                        np.full(dims, np.nan),
                        broadcast=True
                    )
                self.timestamp[seq_name] = None

        elif self.rm in ["camera", "camera_states", "camera_parity"]:
            self.use_camera = True
            self.n_ions = int(self.p.IonsOnCamera.ion_number)
            for seq_name, dims in scan_specs.items():
                if not self.is_ndim:
                    # Currently not supporting any default plotting for (n>1)-dim scans
                    self.average_confidences = np.full(dims, np.nan)
                    if self.rm == "camera":
                        for i in range(self.n_ions):
                            setattr(
                                self,
                                "{}-ion number:{}".format(seq_name, i),
                                np.full(dims, np.nan)
                            )
                    else:
                        self.camera_string_states = self.camera_states_repr(self.n_ions)
                        for state in self.camera_string_states:
                            setattr(
                                self,
                                "{}-{}".format(seq_name, state),
                                np.full(dims, np.nan)
                            )
                        if self.rm == "camera_parity":
                            setattr(self, "{}-parity".format(seq_name), np.full(dims, np.nan))
                    x_array = np.array(list(list(self.multi_scannables[seq_name].values())[0]))
                    self.x_label[seq_name] = [self.selected_scan[seq_name]]
                    f = seq_name + "-" if len(self.scan_params) > 1 else ""
                    f += self.x_label[seq_name][0]
                    setattr(self, f, x_array)
                else:
                    raise NotImplementedError("Ndim scans with camera not implemented yet")
                self.timestamp[seq_name] = None

        # Setup for saving data
        self.filename = dict()
        self.dir = os.path.join(
            os.path.expanduser("~"),
            "data",
            datetime.now().strftime("%Y-%m-%d"), type(self).__name__
        )
        os.makedirs(self.dir, exist_ok=True)
        os.chdir(self.dir)

        # Lists to keep track of current line calibrations
        self.carrier_names = [
            "S+1/2D-3/2",
            "S-1/2D-5/2",
            "S+1/2D-1/2",
            "S-1/2D-3/2",
            "S+1/2D+1/2",
            "S-1/2D-1/2",
            "S+1/2D+3/2",
            "S-1/2D+1/2",
            "S+1/2D+5/2",
            "S-1/2D+3/2"
        ]
        # Convenience dictionary for user sequences
        self.carrier_dict = {
            "S+1/2D-3/2": 0,
            "S-1/2D-5/2": 1,
            "S+1/2D-1/2": 2,
            "S-1/2D-3/2": 3,
            "S+1/2D+1/2": 4,
            "S-1/2D-1/2": 5,
            "S+1/2D+3/2": 6,
            "S-1/2D+1/2": 7,
            "S+1/2D+5/2": 8,
            "S-1/2D+3/2": 9
        }
        self.carrier_values = self.update_carriers()
        self.trap_frequency_names = list()
        self.trap_frequency_values = list()
        for name, value in self.p.TrapFrequencies.items():
            self.trap_frequency_names.append(name)
            self.trap_frequency_values.append(value)

    @classmethod
    def set_global_params(cls):
        cls.accessed_params.update(
            {
                "Display.relative_frequencies",
                "StateReadout.amplitude_397",
                "StateReadout.amplitude_866",
                "StateReadout.att_397",
                "StateReadout.att_866",
                "StateReadout.frequency_397",
                "StateReadout.frequency_866",
                "StateReadout.readout_mode",
                "StateReadout.doppler_cooling_repump_additional",
                "StateReadout.frequency_397",
                "StatePreparation.sideband_cooling_enable",
                "StatePreparation.pulsed_optical_pumping",
                "StatePreparation.optical_pumping_enable",
                "StatePreparation.channel_729"
            }
        )

    def run(self):
        if self.rm in ["camera", "camera_states", "camera_parity"]:
            self.initialize_camera()
        linetrigger = self.p.line_trigger_settings.enabled
        linetrigger_offset = float(self.p.line_trigger_settings.offset_duration)
        linetrigger_offset = self.core.seconds_to_mu(linetrigger_offset * us)
        is_multi = True if len(self.multi_scannables) > 1 else False
        master_iterable = product(*self.master_scan_iterables)
        for master_scan_values in master_iterable:
            self.timestamp = odict()
            for i, value in enumerate(master_scan_values):
                collection, key = self.master_scan_names[i].split(".")
                self.p[collection][key] = value
            for seq_name, scan_dict in self.multi_scannables.items():
                if (self.rcg_tabs[seq_name][self.selected_scan[seq_name]] in absolute_frequency_plots
                        and not self.p.Display.relative_frequencies):
                    self.set_dataset(seq_name + "-raw_x_data", [], broadcast=True)
                self.variable_parameter_names = [
                    "current_data_point",
                    "current_experiment_iteration"
                ]
                self.variable_parameter_values = [0., 0.]
                self.parameter_names = list()
                self.parameter_values = list()
                scanned_params = set(scan_dict.keys())
                self.set_global_params()
                repump_dc_params = {
                    "RepumpD_5_2.repump_d_frequency_854",
                    "RepumpD_5_2.repump_d_att_854",
                    "RepumpD_5_2.repump_d_amplitude_854",
                    "DopplerCooling.doppler_cooling_frequency_866",
                    "DopplerCooling.doppler_cooling_amplitude_866",
                    "DopplerCooling.doppler_cooling_att_866",
                    "DopplerCooling.doppler_cooling_frequency_397",
                    "DopplerCooling.doppler_cooling_amplitude_397",
                    "DopplerCooling.doppler_cooling_att_397"
                }
                all_accessed_params = self.accessed_params | scanned_params | repump_dc_params
                self.kernel_invariants = set()
                for mode_name, frequency in self.p.TrapFrequencies.items():
                    self.kernel_invariants.update({mode_name})
                    setattr(self, mode_name, frequency)
                abs_freqs = True if self.rcg_tabs[seq_name][
                                        self.selected_scan[seq_name]] in absolute_frequency_plots else False
                self.abs_freqs = abs_freqs
                self.seq_name = seq_name
                self.current_x_value = 9898989898.9898989898
                self.kernel_invariants.update(
                    {
                        "dds_names",
                        "dds_offsets",
                        "dds_dp_flags",
                        "seq_name",
                        "abs_freqs"
                    }
                )
                for param_name in all_accessed_params:
                    collection, key = param_name.split(".")
                    param = self.p[collection][key]
                    new_param_name = param_name.replace(".", "_")
                    if (type(param) is (float or int)) and (param_name in scanned_params):
                        self.variable_parameter_names.append(new_param_name)
                        if self.selected_scan[seq_name] == param_name:
                            self.variable_parameter_values.append(list(scan_dict[param_name])[0])
                        else:
                            collection, parameter = param_name.split(".")
                            self.variable_parameter_values.append(self.p[collection][parameter])
                    else:
                        self.parameter_names.append(param_name)
                        self.parameter_values.append(param)
                        self.kernel_invariants.update({new_param_name})
                        setattr(self, new_param_name, param)

                current_sequence = getattr(self, seq_name)
                selected_scan = self.selected_scan[seq_name]
                self.selected_scan_name = selected_scan.replace(".", "_")
                if not self.is_ndim:
                    scan_iterable = list(scan_dict[selected_scan])
                    self.scan_iterable = scan_iterable
                    ndim_iterable = [[0]]
                else:
                    ms_list = [list(x) for x in scan_dict.values()]
                    ndim_iterable = list(map(list, list(product(*ms_list))))
                    scan_iterable = [0]
                    self.set_dataset("x_data", ndim_iterable)
                scan_names = list(map(lambda x: x.replace(".", "_"), self.x_label[seq_name]))
                self.start_point1, self.start_point2 = 0, 0
                self.run_looper = True
                try:
                    set_subsequence = self.set_subsequence[seq_name]
                except KeyError:
                    @kernel
                    def maybe_needed_delay():
                        delay(.1 * us)

                    set_subsequence = maybe_needed_delay
                if self.use_camera:
                    readout_duration = self.p.StateReadout.camera_readout_duration
                else:
                    readout_duration = self.p.StateReadout.pmt_readout_duration

                while self.run_looper:
                    try:
                        self.looper(
                            current_sequence,
                            self.N,
                            linetrigger,
                            linetrigger_offset,
                            scan_iterable,
                            self.rm,
                            readout_duration,
                            seq_name, is_multi,
                            self.n_ions,
                            self.is_ndim,
                            scan_names,
                            ndim_iterable,
                            self.start_point1,
                            self.start_point2,
                            self.use_camera,
                            set_subsequence
                        )
                    except RTIOUnderflow:
                        logger.error("RTIOUnderflow", exc_info=True)
                        continue
                    except:
                        self.reset_cw_settings(
                            self.dds_list,
                            self.freq_list,
                            self.amp_list,
                            self.state_list,
                            self.att_list
                        )
                        self.reset_camera_settings()
                        raise
                    if self.scheduler.check_pause():
                        try:
                            self.core.comm.close()
                            self.scheduler.pause()
                        except TerminationRequested:
                            try:
                                self.run_after[seq_name]()
                                continue
                            except:
                                self.set_dataset("raw_run_data", None, archive=False)
                                self.reset_cw_settings(
                                    self.dds_list,
                                    self.freq_list,
                                    self.amp_list,
                                    self.state_list,
                                    self.att_list
                                )
                                self.reset_camera_settings()
                                return
                try:
                    self.run_after[seq_name]()
                except FitError:
                    logger.error("Fit failed.", exc_info=True)
                    continue
                except KeyError:
                    continue
                except:
                    logger.error(
                        "run_after failed for seq_name: {}.".format(seq_name),
                        exc_info=True
                    )
                    continue
        self.set_dataset("raw_run_data", None, archive=False)
        self.reset_cw_settings(
            self.dds_list,
            self.freq_list,
            self.amp_list,
            self.state_list,
            self.att_list
        )
        self.reset_camera_settings()

    def reset_camera_settings(self):
        if self.rm in ["camera", "camera_states", "camera_parity"]:
            self.camera.abort_acquisition()
            self.camera.set_trigger_mode(self.initial_trigger_mode)
            self.camera.set_exposure_time(self.initial_exposure)
            self.camera.set_image_region(1, 1, 1, 512, 1, 512)
            self.camera.start_live_display()

    @kernel
    def turn_off_all(self):
        self.core.reset()
        for cpld in self.cpld_list:
            cpld.init()
        for device in self.dds_device_list:
            device.sw.off()

    @kernel
    def setup_ram_modulation(
            self,
            dds,
            modulation_waveform,
            modulation_type="frequency",
            step=1,  # in units of sync_clk cycle, ~4 ns for us
            ram_mode=0,
            nodwell_high=0
    ):
        N = len(modulation_waveform)
        ram_data = [0] * N

        if modulation_type in ["frequency", "freq"]:
            dds.frequency_to_ram(modulation_waveform, ram_data)
            destination = RAM_DEST_FTW
        elif modulation_type in ["amplitude", "amp"]:
            dds.amplitude_to_ram(modulation_waveform, ram_data)
            destination = RAM_DEST_ASF
        elif modulation_type == "phase":
            dds.turns_to_ram(modulation_waveform, ram_data)
            destination = RAM_DEST_POW
        elif modulation_type in ["phase_and_amplitude", "phase_and_amp"]:
            dds.turns_amplitude_to_ram(
                modulation_waveform[0],
                modulation_waveform[1],
                ram_data
            )
            destination = RAM_DEST_POWASF

        dds.cpld.init()
        dds.init()
        dds.set_cfr1(ram_enable=0)
        dds.cpld.set_profile(0)
        dds.cpld.io_update.pulse_mu(8)
        dds.set_profile_ram(
            start=0,
            end=len(ram_data) - 1,
            step=step,
            profile=0,
            mode=ram_mode,
            nodwell_high=nodwell_high
        )
        dds.cpld.io_update_pulse.pulse_mu(8)
        dds.write_ram(ram_data)
        delay(1 * ms)

        dds.set_cfr1(
            ram_enable=1,
            ram_destination=destination,
            phase_autoclear=1,
            # the following parameters are a hack as described in
            # https://github.com/m-labs/artiq/issues/1554
            manual_osk_external=0,
            osk_enable=1 if modulation_type in ["frequency", "freq"] else 0,
            select_auto_osk=0
        )
        dds.cpld.io_update.pulse_mu(8)

    @kernel
    def stop_ram_modulation(self, dds):
        dds.set_cfr1(ram_enable=0)
        dds.cpld.io_update.pulse_mu(8)
        dds.cpld.set_profile(0)
        dds.cpld.io_update.pulse_mu(8)

    @kernel
    def prepare_pulse_with_amplitude_ramp(
            self, pulse_duration, ramp_duration, dds1_amp=0., use_dds2=False, dds2_amp=0.):
        #
        # To be used in combination with execute_pulse_with_amplitude_ramp:
        # - prepare_pulse_with_amplitude_ramp (this function) programs the desired
        #   waveform into the AD9910. This should be run once per data point (i.e.,
        #   once per 100 shots).
        # - execute_pulse_with_amplitude_ramp (the following function) actually
        #   performs the ramp-up, wait, and ramp-down as described below.
        #
        # Pulses the provided DDS channel (or both channels, if two are provided)
        # with a linear amplitude ramp. The amplitude begins at 0, ramps up to
        # the specified amplitude over the time given by ramp_duration, waits,
        # and then ramps down to zero amplitude.
        #
        # The total pulse time, including the ramps, will be pulse_duration.
        #
        # If pulse_duration is less than twice the ramp_duration, the ramp will
        # not reach the full amplitude, but instead will ramp up for half of
        # pulse_duration, and then immediately ramp down for half of pulse_duration.
        #

        # Get the DDS channels.
        ramp_dds1 = self.dds_729
        ramp_dds2 = self.dds_7291

        # Break and delay to avoid RTIO underflow
        self.core.break_realtime()
        delay(12 * ms)

        # Calculate the ramp duration, wait duration, and
        # maximum amplitudes for each channel.
        clock_cycles_per_step = 4
        original_ramp_slope_duration = ramp_duration
        self.ramp_slope_duration = min(original_ramp_slope_duration, pulse_duration)
        # Note: We want the area of this pulse to be equal to the area of a pulse
        # without ramping. The area of both ramp periods is equivalent to the area
        # of a single ramp period at full amplitude. So the wait duration should
        # be the pulse duration minus one ramp duration.
        # Also, empirically (on the scope) we observe that the wait duration is 500 ns too long,
        # so we subtract 500 ns from the wait duration (also ensuring it remains non-negative).
        self.ramp_wait_duration = max(0.0, pulse_duration - self.ramp_slope_duration - 500 * ns)
        dds1_max_amp = dds1_amp * (self.ramp_slope_duration / original_ramp_slope_duration)
        dds2_max_amp = dds2_amp * (self.ramp_slope_duration / original_ramp_slope_duration)

        # Create the list of amplitudes for each ramp. We need four ramps:
        # ramp up and ramp down for each of dds1 and dds2.
        n_steps = min(100, np.int32(round(self.ramp_slope_duration / (clock_cycles_per_step * 5 * ns)))) + 1
        dds1_ramp_up = [dds1_max_amp / n_steps * (float(n_steps - 1) - i) for i in range(n_steps)]
        dds2_ramp_up = [dds2_max_amp / n_steps * (float(n_steps - 1) - i) for i in range(n_steps)]
        dds1_ramp_up_data = [0] * (n_steps)
        dds2_ramp_up_data = [0] * (n_steps)
        dds1_ramp_down_data = [0] * (n_steps)
        dds2_ramp_down_data = [0] * (n_steps)
        # NOTE: The built-in amplitude_to_ram() method does not
        #       comply with the AD9910 specification. Doing this
        #       manually instead, until amplitude_to_ram() is fixed.
        ##### ramp_dds1.amplitude_to_ram(dds1_ramp_up, dds1_ramp_up_data)
        ##### if use_dds2:
        #####   ramp_dds2.amplitude_to_ram(dds2_ramp_up, dds2_ramp_up_data)
        for i in range(len(dds1_ramp_up)):
            dds1_ramp_up_data[i] = (np.int32(round(dds1_ramp_up[i] * 0x3fff)) << 18)
            dds2_ramp_up_data[i] = (np.int32(round(dds2_ramp_up[i] * 0x3fff)) << 18)
        for i in range(len(dds1_ramp_up_data)):
            dds1_ramp_down_data[i] = dds1_ramp_up_data[len(dds1_ramp_up_data) - i - 1]
            dds2_ramp_down_data[i] = dds2_ramp_up_data[len(dds2_ramp_up_data) - i - 1]

        # Print stuff
        # print("ramp_slope_duration:", self.ramp_slope_duration)
        # print("n_steps:", n_steps)
        # print("ramp_wait_duration:", self.ramp_wait_duration)
        # print("dds1_max_amp:", dds1_max_amp)
        # print("dds1_ramp_up:", dds1_ramp_up)
        # print("dds1_ramp_up_data:", dds1_ramp_up_data)
        # print("dds1_ramp_down_data:", dds1_ramp_down_data)
        # self.core.break_realtime()

        # Program the RAM with each waveform.
        start_address = 0
        ramp_dds1.set_profile_ram(start=start_address, end=start_address + n_steps - 1,
                                  step=clock_cycles_per_step, profile=self.dds1_ramp_up_profile, mode=RAM_MODE_RAMPUP)
        ramp_dds1.cpld.set_profile(self.dds1_ramp_up_profile)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        ramp_dds1.write_ram(dds1_ramp_up_data)

        start_address += n_steps
        ramp_dds1.set_profile_ram(start=start_address, end=start_address + n_steps - 1,
                                  step=clock_cycles_per_step, profile=self.dds1_ramp_down_profile, mode=RAM_MODE_RAMPUP)
        ramp_dds1.cpld.set_profile(self.dds1_ramp_down_profile)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        ramp_dds1.write_ram(dds1_ramp_down_data)

        if use_dds2:
            start_address += n_steps
            ramp_dds2.set_profile_ram(start=start_address, end=start_address + n_steps - 1,
                                      step=clock_cycles_per_step, profile=self.dds2_ramp_up_profile,
                                      mode=RAM_MODE_RAMPUP)
            ramp_dds2.cpld.set_profile(self.dds2_ramp_up_profile)
            ramp_dds2.cpld.io_update.pulse_mu(8)
            ramp_dds2.write_ram(dds2_ramp_up_data)

            start_address += n_steps
            ramp_dds2.set_profile_ram(start=start_address, end=start_address + n_steps - 1,
                                      step=clock_cycles_per_step, profile=self.dds2_ramp_down_profile,
                                      mode=RAM_MODE_RAMPUP)
            ramp_dds2.cpld.set_profile(self.dds2_ramp_down_profile)
            ramp_dds2.cpld.io_update.pulse_mu(8)
            ramp_dds2.write_ram(dds2_ramp_down_data)

        # Reset to profile 0 so we don't affect the next experiment.
        ramp_dds1.cpld.set_profile(0)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        if use_dds2:
            ramp_dds2.cpld.set_profile(0)
            ramp_dds2.cpld.io_update.pulse_mu(8)

    @kernel
    def execute_pulse_with_amplitude_ramp(
            self, dds1_att=8 * dB, dds1_freq=220 * MHz,
            use_dds2=False, dds2_att=8 * dB, dds2_freq=220 * MHz):
        #
        # To be used in combination with prepare_pulse_with_amplitude_ramp.
        # See the comments in that function for details.
        #

        # Get the DDS channels.
        ramp_dds1 = self.dds_729
        ramp_dds2 = self.dds_7291

        # Print stuff
        # print("ramp_slope_duration:", self.ramp_slope_duration)
        # print("ramp_wait_duration:", self.ramp_wait_duration)
        # self.core.break_realtime()

        # Start by disabling ramping and resetting to profile 0.
        ramp_dds1.set_cfr1(ram_enable=0)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        ramp_dds1.cpld.set_profile(0)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        if use_dds2:
            ramp_dds2.set_cfr1(ram_enable=0)
            ramp_dds2.cpld.io_update.pulse_mu(8)
            ramp_dds2.cpld.set_profile(0)
            ramp_dds2.cpld.io_update.pulse_mu(8)

        # Set the desired initial parameters and turn on each DDS.
        ramp_dds1.set_frequency(dds1_freq)
        ramp_dds1.set_amplitude(0.)
        ramp_dds1.set_att(dds1_att)
        ramp_dds1.sw.on()
        if use_dds2:
            ramp_dds2.set_frequency(dds2_freq)
            ramp_dds2.set_amplitude(0.)
            ramp_dds2.set_att(dds2_att)
            ramp_dds2.sw.on()

        # Set the current profile to the ramp-up profile constructed above.
        ramp_dds1.cpld.set_profile(self.dds1_ramp_up_profile)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        if use_dds2:
            ramp_dds2.cpld.set_profile(self.dds2_ramp_up_profile)
            ramp_dds2.cpld.io_update.pulse_mu(8)

        # Enable the ramping, which immediately starts playing the ramp waveform.
        ramp_dds1.set_cfr1(ram_enable=1, ram_destination=RAM_DEST_ASF)
        if use_dds2:
            ramp_dds2.set_cfr1(ram_enable=1, ram_destination=RAM_DEST_ASF)
            with parallel:
                ramp_dds1.cpld.io_update.pulse_mu(8)
                ramp_dds2.cpld.io_update.pulse_mu(8)
        else:
            ramp_dds1.cpld.io_update.pulse_mu(8)

        # Wait for the ramp to finish.
        delay(self.ramp_slope_duration)

        # Wait for the desired time.
        delay(self.ramp_wait_duration)

        # Activate the ramp-down profiles, which immediately begins the ramp down.
        ramp_dds1.cpld.set_profile(self.dds1_ramp_down_profile)
        if use_dds2:
            ramp_dds2.cpld.set_profile(self.dds2_ramp_down_profile)
            with parallel:
                ramp_dds1.cpld.io_update.pulse_mu(8)
                ramp_dds2.cpld.io_update.pulse_mu(8)
        else:
            ramp_dds1.cpld.io_update.pulse_mu(8)

        # Wait for the ramp to finish, plus some extra time to be safe.
        delay(2 * self.ramp_slope_duration)

        # Turn off the DDS outputs.
        # ramp_dds1.sw.off()
        # if use_dds2:
        #    ramp_dds2.sw.off()

        # Disable ramping so we don't affect the next experiment.
        # Also reset to profile 0.
        ramp_dds1.set_cfr1(ram_enable=0)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        ramp_dds1.cpld.set_profile(0)
        ramp_dds1.cpld.io_update.pulse_mu(8)
        if use_dds2:
            ramp_dds2.set_cfr1(ram_enable=0)
            ramp_dds2.cpld.io_update.pulse_mu(8)
            ramp_dds2.cpld.set_profile(0)
            ramp_dds2.cpld.io_update.pulse_mu(8)

    @kernel
    def line_trigger(self, offset):
        # Phase lock to mains
        self.core.reset()
        trigger_time = -1
        while True:
            with parallel:
                t_gate = self.linetrigger_ttl.gate_rising(2 * ms)
                trigger_time = self.linetrigger_ttl.timestamp_mu(t_gate)
            if trigger_time == -1:
                delay(6 * us)
                continue
            break
        at_mu(trigger_time + offset)

    @kernel
    def looper(
            self, sequence, reps, linetrigger, linetrigger_offset, scan_iterable,
            readout_mode, readout_duration, seq_name, is_multi, number_of_ions,
            is_ndim, scan_names, ndim_iterable, start1, start2, use_camera,
            set_subsequence
    ):
        self.turn_off_all()
        self.dds_854.set(
            self.RepumpD_5_2_repump_d_frequency_854,
            amplitude=self.RepumpD_5_2_repump_d_amplitude_854
        )
        self.dds_854.set_att(self.RepumpD_5_2_repump_d_att_854)
        self.dds_866.set(
            self.DopplerCooling_doppler_cooling_frequency_866,
            amplitude=self.DopplerCooling_doppler_cooling_amplitude_866
        )
        self.dds_866.set_att(self.DopplerCooling_doppler_cooling_att_866)
        self.dds_397.set(
            self.DopplerCooling_doppler_cooling_frequency_397,
            amplitude=self.DopplerCooling_doppler_cooling_amplitude_397
        )
        self.dds_397.set_att(self.DopplerCooling_doppler_cooling_att_397)
        with parallel:
            self.dds_854.sw.on()
            self.dds_866.sw.on()
            self.dds_397.sw.on()

        i = 0
        for i in list(range(len(scan_iterable)))[start1:]:
            self.set_start_point(1, i)
            if self.scheduler.check_pause():
                return
            if use_camera:
                self.prepare_camera()
            self.set_variable_parameter("current_data_point", i * 1.)
            for l in list(range(2, len(self.variable_parameter_names))):
                self.set_variable_parameter(
                    self.variable_parameter_names[l],
                    scan_iterable[i]
                )
            set_subsequence()

            # DMA option
            # -------------------------------------------------------------------------------
            # # Record the pulse sequence. This doesn't actually execute it, just
            # # programs it into memory for later execution.
            # trace_name = "PulseSequence"
            # with self.core_dma.record(trace_name):
            #     delay(20*us)
            #     self.dds_397.sw.off()
            #     delay(20*us)
            #     with parallel:
            #         self.dds_854.sw.off()
            #         self.dds_866.sw.off()
            #     sequence()
            #     delay(5*us)
            #     self.dds_397.set(self.StateReadout_frequency_397,
            #                     amplitude=self.StateReadout_amplitude_397)
            #     delay(5*us)
            #     self.dds_397.set_att(self.StateReadout_att_397)
            #     delay(5*us)
            #     self.dds_866.set(self.StateReadout_frequency_866,
            #                     amplitude=self.StateReadout_amplitude_866)
            #     delay(5*us)
            #     self.dds_866.set_att(self.StateReadout_att_866)
            #     delay(5*us)
            #     self.dds_854.set(self.RepumpD_5_2_repump_d_frequency_854,
            #              amplitude=self.RepumpD_5_2_repump_d_amplitude_854)
            #     delay(10*us)
            #     self.dds_854.set_att(self.RepumpD_5_2_repump_d_att_854)
            #     with parallel:
            #         self.dds_397.sw.on()
            #         self.dds_866.sw.on()
            #     # at_mu(now_mu())
            #     # self.core.wait_until_mu(now_mu())
            #     delay(10*us)

            # pulse_sequence_handle = self.core_dma.get_handle(trace_name)
            # self.core.break_realtime()

            # for j in range(reps):
            #     # # Line trigger, if desired.
            #     if linetrigger:
            #         self.line_trigger(linetrigger_offset)
            #     else:
            #         self.core.break_realtime()

            #     # print("real now: ", now_mu())
            #     # This executes the full pre-recorded pulse sequence.
            #     self.core_dma.playback_handle(pulse_sequence_handle)
            # -------------------------------------------------------------------------------

            for j in range(reps):
                self.set_variable_parameter("current_experiment_iteration", j * 1.)

                # Line trigger, if desired.
                if linetrigger:
                    self.line_trigger(linetrigger_offset)
                else:
                    self.core.break_realtime()

                delay(500 * us)  # extra slack
                self.dds_397.sw.off()
                with parallel:
                    self.dds_854.sw.off()
                    self.dds_866.sw.off()

                sequence()

                self.dds_397.set(
                    self.StateReadout_frequency_397,
                    amplitude=self.StateReadout_amplitude_397
                )
                self.dds_397.set_att(self.StateReadout_att_397)
                self.dds_866.set(
                    self.StateReadout_frequency_866,
                    amplitude=self.StateReadout_amplitude_866
                )
                self.dds_866.set_att(self.StateReadout_att_866)
                self.dds_854.set(
                    self.RepumpD_5_2_repump_d_frequency_854,
                    amplitude=self.RepumpD_5_2_repump_d_amplitude_854
                )
                self.dds_854.set_att(self.RepumpD_5_2_repump_d_att_854)
                with parallel:
                    self.dds_397.sw.on()
                    self.dds_866.sw.on()

                # Readout.
                if not use_camera:
                    if readout_mode == "pmtMLE":
                        nbins = int(readout_duration // 1e-5)
                        for l in range(nbins):
                            pmt_count = self.pmt.count(self.pmt.gate_rising(0 * us))
                            delay(20 * us)
                            self.record_result("mledata", l, pmt_count)
                    else:
                        pmt_count = self.pmt.count(self.pmt.gate_rising(readout_duration))
                        delay(readout_duration)
                        self.record_result("raw_run_data", j, pmt_count)
                else:
                    self.camera_ttl.pulse(500 * us)
                    self.core.wait_until_mu(now_mu())
                    delay(readout_duration)

                self.dds_854.sw.on()

            # DMA option
            # -------------------------------------------------------------------------------
            # Pulse sequence repetitions are complete, so free up the DMA memory.
            # self.core_dma.erase(trace_name)
            # -------------------------------------------------------------------------------

            # Process readout data now that all repetitions of the pulse sequence
            # have been completed.
            if not use_camera:
                self.update_raw_data(seq_name, i)
                if readout_mode == "pmt":
                    self.update_pmt(seq_name, i, is_multi)
                elif readout_mode == "pmtMLE":
                    self.update_pmt(seq_name, i, is_multi)
                elif readout_mode == "pmt_parity":
                    self.update_pmt(seq_name, i, is_multi, with_parity=True)
            elif (readout_mode == "camera" or
                  readout_mode == "camera_states" or
                  readout_mode == "camera_parity"):
                self.update_camera(seq_name, i, is_multi, readout_mode)

            rem = (i + 1) % 5
            if rem == 0:
                if (i + 1) == len(scan_iterable):
                    edge = True
                    i = 4
                else:
                    edge = False
                self.update_carriers_on_kernel(self.update_carriers())
                if not use_camera:
                    self.save_result(seq_name, is_multi, xdata=True, i=i, edge=edge)
                    self.send_to_hist(seq_name, i, edge=edge)
                    for k in range(number_of_ions):
                        self.save_result(seq_name + "-dark_ions:", is_multi, i=i, index=k,
                                         edge=edge)
                    if readout_mode == "pmt_parity":
                        self.save_result(seq_name + "-parity", is_multi, i=i, edge=edge)
                else:
                    if readout_mode == "camera":
                        for k in range(number_of_ions):
                            self.save_result(seq_name + "-ion number:", is_multi, i=i,
                                             index=k, edge=edge)
                    else:
                        for state in self.camera_string_states:
                            self.save_result(seq_name + "-" + state, is_multi, i=i, edge=edge)
                        if readout_mode == "camera_parity":
                            self.save_result(seq_name + "-parity", is_multi, i=i, edge=edge)

        else:
            self.set_run_looper_off()
            rem = (i + 1) % 5
            if rem == 0:
                return
            if not use_camera:
                self.send_to_hist(seq_name, rem, edge=True)
                self.save_result(seq_name, is_multi, xdata=True, i=rem, edge=True)
                for k in range(number_of_ions):
                    self.save_result(seq_name + "-dark_ions:", is_multi, i=i, index=k,
                                     edge=True)
                if readout_mode == "pmt_parity":
                    self.save_result(seq_name + "-parity", is_multi, i=i, edge=True)
            else:
                if readout_mode == "camera":
                    for k in range(number_of_ions):
                        self.save_result(seq_name + "-ion number:", is_multi, i=i,
                                         index=k, edge=True)
                else:
                    for state in self.camera_string_states:
                        self.save_result(seq_name + "-" + state, is_multi, i=i, edge=True)
                    if readout_mode == "camera_parity":
                        self.save_result(seq_name + "-parity", is_multi, i=i, edge=True)

    def set_start_point(self, point, i):
        if point == 1:
            self.start_point1 = i
        if point == 2:
            self.start_point2 = i

    def set_run_looper_off(self):
        self.run_looper = False

    @rpc(flags={"async"})
    def update_pmt(self, seq_name, i, is_multi, with_parity=False):
        data = sorted(self.get_dataset(seq_name + "-raw_data")[i])
        thresholds = self.p.StateReadout.threshold_list
        name = seq_name + "-dark_ions:{}"
        idxs = [0]
        scan_name = self.selected_scan_name.replace("_", ".", 1)
        scanned_x = list(self.multi_scannables[seq_name][scan_name])
        if isinstance(self.multi_scannables[seq_name][scan_name], scan.NoScan):
            scanned_x = np.linspace(0, len(scanned_x), len(scanned_x))
        if self.abs_freqs and not self.p.Display.relative_frequencies:
            x = [i * 1e-6 for i in self.get_dataset(seq_name + "-raw_x_data")]
            if seq_name not in self.range_guess.keys():
                try:
                    self.range_guess[seq_name] = x[0], x[0] + (scanned_x[-1] - scanned_x[0]) * 1e-6
                except IndexError:
                    self.range_guess[seq_name] = None
        else:
            x = scanned_x
            if seq_name not in self.range_guess.keys():
                self.range_guess[seq_name] = x[0], x[-1]
            x = x[:i + 1]
        for threshold in thresholds:
            idxs.append(bisect(data, threshold))
        idxs.append(self.N)
        parity = 0
        for k in range(self.n_ions):
            dataset = getattr(self, name.format(k))
            if idxs[k + 1] == idxs[k]:
                dataset[i] = 0
            else:
                dataset[i] = (idxs[k + 1] - idxs[k]) / self.N
            if k % 2 == 0:
                parity += dataset[i]
            else:
                parity -= dataset[i]
            # For some reason, when using master scans, xdata for consecutive runs is
            # appended. Need to figure out why, but for now this will do.
            if len(x) != len(dataset[:i + 1]):
                x = x[-len(dataset[:i + 1]):]
            self.save_and_send_to_rcg(
                x, dataset[:i + 1],
                name.split("-")[-1].format(k),
                seq_name, is_multi,
                self.range_guess[seq_name]
            )
        if with_parity:
            dataset = getattr(self, seq_name + "-parity")
            dataset[i] = parity
            self.save_and_send_to_rcg(
                x,
                dataset[:i + 1],
                "parity",
                seq_name,
                is_multi,
                self.range_guess[seq_name]
            )

    def output_images_to_file(self, images, seq_name, i):
        image_region = [int(self.p.IonsOnCamera.horizontal_bin),
                        int(self.p.IonsOnCamera.vertical_bin),
                        int(self.p.IonsOnCamera.horizontal_min),
                        int(self.p.IonsOnCamera.horizontal_max),
                        int(self.p.IonsOnCamera.vertical_min),
                        int(self.p.IonsOnCamera.vertical_max),
                        ]
        x_pixels = int((image_region[3] - image_region[2] + 1.) / (image_region[0]))
        y_pixels = int((image_region[5] - image_region[4] + 1.) / (image_region[1]))
        images = np.reshape(images, (self.N, y_pixels, x_pixels))
        if seq_name not in self.timestamp.keys():
            self.timestamp[seq_name] = None
        if self.timestamp[seq_name] is None:
            self.start_time = datetime.now()
        with h5.File(self.start_time.strftime("%H%M_%S") + "_images.h5", "a") as f:
            if "images" not in f.keys():
                images_group = f.create_group("images")
            else:
                images_group = f["images"]
            datapoint_group = images_group.create_group("datapoint" + str(i))
            datapoint_group.attrs["image_count"] = len(images)
            for image_idx, image in enumerate(images):
                datapoint_group.create_dataset(str(image_idx), data=image)

    # Need this to be a blocking call #
    def update_camera(self, seq_name, i, is_multi, readout_mode):
        images = []
        try:
            timeout_in_seconds = 60
            images = self.camera.get_acquired_data(timeout_in_seconds)
        except Exception as e:
            self.analyze()
            logger.error(e)
            raise Exception("Camera acquisition timed out")

        # Uncomment this line to write all of the camera images to an .h5 file
        # self.output_images_to_file(images, seq_name, i)

        self.camera.abort_acquisition()
        ion_state, camera_readout, confidences = readouts.camera_ion_probabilities(images,
                                                                                   self.N, self.p.IonsOnCamera,
                                                                                   readout_mode)
        self.average_confidences[i] = np.mean(confidences)
        scan_name = self.selected_scan_name.replace("_", ".", 1)
        scanned_x = list(self.multi_scannables[seq_name][scan_name])
        if isinstance(self.multi_scannables[seq_name][scan_name], scan.NoScan):
            scanned_x = np.linspace(0, len(scanned_x), len(scanned_x))
        if self.abs_freqs and not self.p.Display.relative_frequencies:
            x = [i * 1e-6 for i in self.get_dataset(seq_name + "-raw_x_data")]
            if seq_name not in self.range_guess.keys():
                self.range_guess[seq_name] = x[0], x[0] + (scanned_x[-1] - scanned_x[0]) * 1e-6
        else:
            x = scanned_x
            if seq_name not in self.range_guess.keys():
                self.range_guess[seq_name] = x[0], x[-1]
            x = x[:i + 1]
        if readout_mode == "camera":
            name = seq_name + "-ion number:{}"
            for k in range(self.n_ions):
                # For some reason, when using master scans, xdata for consecutive runs is
                # appended. Need to figure out why, but for now this will do.
                dataset = getattr(self, name.format(k))
                if len(x) != len(dataset[:i + 1]):
                    x = x[-len(dataset[:i + 1]):]
                dataset[i] = ion_state[k]
                self.save_and_send_to_rcg(
                    x,
                    dataset[:i + 1],
                    name.split("-")[-1].format(k),
                    seq_name, is_multi,
                    self.range_guess[seq_name]
                )
        elif readout_mode == "camera_states" or readout_mode == "camera_parity":
            name = seq_name + "-{}"
            for k, state in enumerate(self.camera_states_repr(self.n_ions)):
                # For some reason, when using master scans, xdata for consecutive runs is
                # appended. Need to figure out why, but for now this will do.
                dataset = getattr(self, name.format(self.camera_string_states[k]))
                if len(x) != len(dataset[:i + 1]):
                    x = x[-len(dataset[:i + 1]):]
                dataset[i] = ion_state[k]
                self.save_and_send_to_rcg(
                    x,
                    dataset[:i + 1],
                    name.split("-")[-1].format(state),
                    seq_name, is_multi,
                    self.range_guess[seq_name]
                )
            if readout_mode == "camera_parity":
                # For some reason, when using master scans, xdata for consecutive runs is
                # appended. Need to figure out why, but for now this will do.
                dataset = getattr(self, name.format("parity"))
                if len(x) != len(dataset[:i + 1]):
                    x = x[-len(dataset[:i + 1]):]
                dataset[i] = ion_state[-1]
                self.save_and_send_to_rcg(x, dataset[:i + 1], "parity",
                                          seq_name, is_multi, self.range_guess[seq_name])

    @rpc(flags={"async"})
    def save_and_send_to_rcg(self, x, y, name, seq_name, is_multi, range_guess=None):
        if seq_name not in self.timestamp.keys():
            self.timestamp[seq_name] = None
        if self.timestamp[seq_name] is None:
            self.start_time = datetime.now()
            self.timestamp[seq_name] = self.start_time.strftime("%H%M_%S")
            self.filename[seq_name] = self.timestamp[seq_name] + ".h5"
            with h5.File(self.filename[seq_name], "w") as f:
                datagrp = f.create_group("scan_data")
                datagrp.attrs["plot_show"] = self.rcg_tabs[seq_name][self.selected_scan[seq_name]]
                params = f.create_group("parameters")
                for collection in self.p.keys():
                    collectiongrp = params.create_group(collection)
                    for key, val in self.p[collection].items():
                        collectiongrp.create_dataset(key, data=str(val))
            with open("../scan_list", "a+") as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                cls_name = type(self).__name__
                if is_multi:
                    cls_name += "_" + seq_name
                csvwriter.writerow([self.timestamp[seq_name], cls_name,
                                    os.path.join(self.dir, self.filename[seq_name])])
            self.save_result(seq_name, is_multi, xdata=True)
        delta = datetime.now() - self.start_time
        self.append_to_dataset("time", delta.total_seconds())
        if self.rcg is None:
            try:
                self.rcg = Client("::1", 3286, "rcg")
            except:
                return
        try:
            if self.master_scans:
                title = self.timestamp[seq_name] + " - " + name + " ({})".format(seq_name)
            else:
                title = self.timestamp[seq_name] + " - " + name
            self.rcg.plot(
                x, y,
                tab_name=self.rcg_tabs[seq_name][self.selected_scan[seq_name]],
                plot_title=title,
                append=True,
                file_=os.path.join(os.getcwd(),
                                   self.filename[seq_name]),
                range_guess=range_guess
            )
        except:
            return

    def manual_save(self, x, y, name=None, plot_window="Current",
                    xlabel="x", ylabel="y"):
        # convenience function
        if name is None:
            name = datetime.now().strftime("%H%M_%S")
        with h5.File(name + ".h5", "w") as f:
            datagrp = f.create_group("scan_data")
            datagrp.attrs["plot_show"] = plot_window
            datagrp = f["scan_data"]
            try:
                del datagrp[xlabel]
            except:
                pass
            try:
                del datagrp[ylabel]
            except:
                pass
            xdata = datagrp.create_dataset(xlabel, data=x)
            xdata.attrs["x-axis"] = True
            datagrp.create_dataset(ylabel, data=y)

    @kernel
    def get_variable_parameter(self, name) -> TFloat:
        value = 0.
        for i in list(range(len(self.variable_parameter_names))):
            if name == self.variable_parameter_names[i]:
                value = self.variable_parameter_values[i]
                break
        else:
            exc = name + " is not a scannable parameter."
            self.host_exception(exc)
        return value

    @kernel
    def set_variable_parameter(self, name, value):
        for i in list(range(len(self.variable_parameter_names))):
            if (name != self.selected_scan_name and
                    name != "current_data_point" and
                    name != "current_experiment_iteration"):
                break
            if name == self.variable_parameter_names[i]:
                self.variable_parameter_values[i] = value
                break

    def host_exception(self, exc) -> TNone:
        raise Exception(exc)

    @kernel
    def reset_cw_settings(self, dds_list, freq_list, amp_list, state_list, att_list):
        # Return the CW settings to what they were when prepare stage was run
        self.core.reset()
        self.camera_ttl.off()
        for cpld in self.cpld_list:
            cpld.init()
        self.core.break_realtime()
        for i in range(len(dds_list)):
            self.core.break_realtime()
            try:
                dds_list[i].init()
            except RTIOUnderflow:
                self.core.break_realtime()
                dds_list[i].init()
            dds_list[i].set(freq_list[i], amplitude=amp_list[i])
            dds_list[i].set_att(att_list[i] * dB)
            if state_list[i]:
                dds_list[i].sw.on()
            else:
                dds_list[i].sw.off()
        self.camera_ttl.off()

    @rpc(flags={"async"})
    def record_result(self, dataset, idx, val):
        self.mutate_dataset(dataset, idx, val)

    @rpc(flags={"async"})
    def append_result(self, dataset, val):
        self.append_to_dataset(dataset, val)

    @rpc(flags={"async"})
    def update_raw_data(self, seq_name, i):
        raw_run_data = self.get_dataset("raw_run_data")
        self.record_result(seq_name + "-raw_data", i, raw_run_data)

    @rpc(flags={"async"})
    def save_result(self, name, is_multi, xdata=False, i="", index=None, edge=False):
        seq_name = name.split("-")[0]
        if index is not None:
            name += str(index)
        if xdata:
            try:
                x_label = self.x_label[name][0]
            except:
                x_label = "x"
            if self.abs_freqs and not self.p.Display.relative_frequencies:
                data = np.array(
                    [i * 1e-6 for i in self.get_dataset(seq_name + "-raw_x_data")]
                )
            else:
                data = getattr(self, seq_name + "-" + x_label if is_multi else x_label)
            dataset = self.x_label[name][0]
            self.data[seq_name]["x"] = data  # This will fail for ndim scans
        else:
            data = getattr(self, name)
            dataset = name
            try:
                self.data[seq_name]["y"][k] = data
            except:
                self.data[seq_name]["y"].append(data)  # This will fail for ndim scans
        with h5.File(self.filename[seq_name], "a") as f:
            datagrp = f["scan_data"]
            try:
                del datagrp[dataset]
            except:
                pass
            data = datagrp.create_dataset(dataset, data=data, maxshape=(None,))
            if xdata:
                data.attrs["x-axis"] = True

    @rpc(flags={"async"})
    def send_to_hist(self, seq_name, i, edge=False):
        data = self.get_dataset(seq_name + "-raw_data")
        if edge:
            data = data[-i:]
        else:
            try:
                data = data[i - 4:i + 1]
            except IndexError:
                data = data[i - 4:]
        self.pmt_hist.plot(data.flatten())

    @kernel
    def calc_frequency(self, line, detuning=0.,
                       sideband="", order=0., dds="", bound_param="") -> TFloat:
        relative_display = self.Display_relative_frequencies
        freq = detuning
        abs_freq = 0.
        line_set = False
        sideband_set = True if sideband == "" else False
        for i in range(10):
            if line == self.carrier_names[i]:
                freq += self.carrier_values[i]
                line_set = True
            if sideband != "" and i <= len(self.trap_frequency_names) - 1:
                if sideband == self.trap_frequency_names[i]:
                    freq += self.trap_frequency_values[i] * order
                    sideband_set = True
            if line_set and sideband_set:
                abs_freq = freq
                break
        if dds != "":
            for i in range(len(self.dds_names)):
                if dds == self.dds_names[i]:
                    freq += self.dds_offsets[i] * 1e6
                    if self.dds_dp_flags[i]:
                        freq /= 2
        if self.abs_freqs and bound_param != "" and not relative_display:
            if self.current_x_value == abs_freq:
                return 220 * MHz - freq
            else:
                self.current_x_value = abs_freq
            for i in list(range(len(self.variable_parameter_names))):
                if bound_param == self.variable_parameter_names[i]:
                    self.append_result(self.seq_name + "-raw_x_data", abs_freq)
                    break
        return 220 * MHz - freq

    @portable
    def get_trap_frequency(self, name) -> TFloat:
        freq = 0.
        for i in range(len(self.trap_frequency_names)):
            if self.trap_frequency_names[i] == name:
                freq = self.trap_frequency_values[i]
                return freq
        return 0.

    @kernel
    def bind_param(self, name, value):
        if self.selected_scan_name == name:
            self.append_result(self.seq_name + "-raw_x_data", value)

    # @rpc(flags={"async"})  Can't use async call if function returns non-None value
    def update_carriers(self) -> TList(TFloat):
        current_lines = self.sd_tracker.get_current_lines(dt_config.client_name)
        _list = [0.] * 10
        for carrier, frequency in current_lines:
            units = frequency.units
            abs_freq = frequency[units] * self.G[units]
            for i in range(10):
                if carrier == self.carrier_names[i]:
                    _list[i] = abs_freq
                    break
        return _list

    @kernel
    def update_carriers_on_kernel(self, new_carrier_values):
        for i in list(range(10)):
            self.carrier_values[i] = new_carrier_values[i]

    @kernel
    def get_offset_frequency(self, name) -> TFloat:
        offset_frequency = 0.
        for i in range(len(self.dds_names)):
            if self.dds_names[i] == name:
                offset_frequency = self.dds_offsets[i] * MHz
                break
        return offset_frequency

    @kernel
    def get_729_dds(self, name="729G", id=0):
        # Need to find a better way to do this
        if id == 0:
            self.dds_729 = self.dds_729G if name == "729G" else self.dds_729L1 if name == "729L1" else self.dds_729L2
            self.dds_729_SP = self.dds_SP_729G if name == "729G" else self.dds_SP_729L1 if name == "729L1" else self.dds_SP_729L2
            self.dds_729_SP_bichro = self.dds_SP_729G_bichro if name == "729G" else self.dds_SP_729L1_bichro if name == "729L1" else self.dds_SP_729L2_bichro
        elif id == 1:
            self.dds_7291 = self.dds_729G if name == "729G" else self.dds_729L1 if name == "729L1" else self.dds_729L2
            self.dds_729_SP1 = self.dds_SP_729G if name == "729G" else self.dds_SP_729L1 if name == "729L1" else self.dds_SP_729L2
            self.dds_729_SP_bichro1 = self.dds_SP_729G_bichro if name == "729G" else self.dds_SP_729L1_bichro if name == "729L1" else self.dds_SP_729L2_bichro
        elif id == 2:
            self.dds_729 = self.dds_729G
            self.dds_729_SP_line1 = self.dds_SP_729G
            self.dds_729_SP_line1_bichro = self.dds_SP_729G_bichro
            self.dds_729_SP_line2 = self.dds_SP_729L2
            self.dds_729_SP_line2_bichro = self.dds_SP_729L2_bichro

    def prepare_camera(self):
        self.camera.abort_acquisition()
        self.camera.set_number_images_to_acquire(self.N)
        self.camera.start_acquisition()

    def initialize_camera(self):
        if not self.camera:
            self.camera = self.cxn.nuvu_camera_server

        self.camera.abort_acquisition()
        self.initial_exposure = self.camera.get_exposure_time()
        exposure = self.p.StateReadout.camera_readout_duration
        p = self.p.IonsOnCamera
        self.image_region = [int(p.horizontal_bin),
                             int(p.vertical_bin),
                             int(p.horizontal_min),
                             int(p.horizontal_max),
                             int(p.vertical_min),
                             int(p.vertical_max)]
        self.camera.set_image_region(*self.image_region)
        self.camera.set_exposure_time(exposure)
        self.initial_trigger_mode = self.camera.get_trigger_mode()
        self.camera.set_trigger_mode("EXT_LOW_HIGH")

    def camera_states_repr(self, N):
        str_repr = []
        for name in range(2 ** N):
            bin_rep = np.binary_repr(name, N)
            state = ""
            for j in bin_rep[::-1]:
                state += "S" if j == "0" else "D"
            str_repr.append(state)
        return str_repr

    def analyze(self):
        try:
            self.run_finally()
        except FitError:
            logger.error("Final fit failed.", exc_info=True)
        except:
            pass
        self.cxn.disconnect()
        self.global_cxn.disconnect()
        try:
            self.rcg.close_rpc()
            self.pmt_hist.close_rpc()
        except:
            pass

    @classmethod
    def initialize_parameters(cls):
        for class_ in EnvExperiment.__subclasses__():
            cls.accessed_params.update(class_.accessed_params)

    def _set_subsequence_defaults(self, subsequence):
        d = subsequence.__dict__
        kwargs = dict()
        for key, value in d.items():
            if type(value) == str:
                try:
                    c, v = value.split(".")
                except AttributeError:
                    continue
                except ValueError:
                    continue
                try:
                    pv_value = self.p[c][v]
                except KeyError:
                    # TODO Ryan fix this - throw if a parameter isn't found
                    # raise Exception("Failed to find parameter: " + value)
                    continue
                try:
                    pv_value = float(pv_value)
                except:
                    pass
                kwargs[key] = pv_value
        for key, value in kwargs.items():
            setattr(subsequence, key, value)

    def add_subsequence(self, subsequence):
        self._set_subsequence_defaults(subsequence)
        subsequence.run = kernel(subsequence.subsequence)
        try:
            subsequence.add_child_subsequences(self)
        except AttributeError:
            pass
        return subsequence

    def update_scan_params(self, scan_params, iteration=None):
        for seq_name, scan_list in scan_params.items():
            if iteration is not None:
                seq_name += str(iteration)
            self.rcg_tabs[seq_name] = odict()
            self.multi_scannables[seq_name] = odict()
            scan_names = list()
            for scan_descr in scan_list:
                rcg_tab, scan_param = scan_descr
                self.rcg_tabs[seq_name][scan_param[0]] = rcg_tab
                scan_names.append(scan_param[0])
                scan_name = seq_name + ":" + scan_param[0]
                if len(scan_param) == 4:
                    scannable = scan.Scannable(default=scan.RangeScan(*scan_param[1:]))
                elif len(scan_param) == 5:
                    scannable = scan.Scannable(
                        default=scan.RangeScan(*scan_param[1:-1]),
                        unit=scan_param[-1]
                    )
                self.multi_scannables[seq_name].update(
                    {scan_param[0]: self.get_argument(scan_name, scannable, group=seq_name)})
            self.selected_scan[seq_name] = self.get_argument(
                seq_name + "-Scan_Selection",
                EnumerationValue(scan_names),
                group=seq_name
            )

    def run_in_build(self):
        pass

    def run_initially(self):
        pass

    def sequence(self):
        raise NotImplementedError

    def run_finally(self):
        pass


class FitError(Exception):
    pass