"""
Calibration sequence to get the relevant amplitude scaling factors for the probe beam for
the temperature measurement experiment.
"""

import labrad
from time import sleep

from numpy import linspace, abs
from EGGS_labrad.clients import createTrunk


# parameters
name_tmp = 'Temperature Measurement Calibration'
dds_name = 'urukul1_ch0'
freq_range_hz = linspace(87.5, 137.5, 23) * 1e6
amp_range_pct = [0, 0.5]
att_db = 14

target_power_uw = 100
tolerance_power_uw = 3
target_wavelength_nm = 400
num_averages = 100


#  main sequence
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    aq = cxn.artiq_server
    pm = cxn.power_meter_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up power meter for 397nm probe beam
    pm.select_device()
    pm.configure_wavelength(target_wavelength_nm)
    pm.configure_autoranging(True)
    pm.configure_averaging(num_averages)
    print("Power meter setup successful.")

    # set up 397nm probe beam
    aq.dds_toggle(dds_name, True)
    aq.dds_attenuation(dds_name, att_db)
    print("Urukul setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'Temperature Measurement Calibration',
        [('DDS Frequency', 'Hz')],
        [('DDS Amplitude', 'Amplitude', 'pct')],
        context=cr
    )
    dv.add_parameter("PM100D Averages", num_averages, context=cr)
    dv.add_parameter("Target Power (uW)", target_power_uw, context=cr)
    dv.add_parameter("Search Tolerance (uW)", tolerance_power_uw, context=cr)
    print("Dataset successfully created.")


    # create recursive binary search function
    def recursion_search(amp_min_pct, amp_max_pct):
        # set asf and get power
        amp_tmp_pct = 0.5 * (amp_min_pct + amp_max_pct)
        aq.dds_amplitude(dds_name, amp_tmp_pct)
        sleep(0.5)
        pow_tmp_uw = pm.measure() * 1e6

        # tmp remove
        #print('[min, max]: {}'.format((amp_min_pct, amp_max_pct)))
        #print('pow_tmp_uw: {}'.format(pow_tmp_uw))

        # return target value
        if abs(pow_tmp_uw - target_power_uw) <= tolerance_power_uw:
            return amp_tmp_pct
        elif pow_tmp_uw < target_power_uw:
            return recursion_search(amp_tmp_pct, amp_max_pct)
        else:
            return recursion_search(amp_min_pct, amp_tmp_pct)


    # sweep frequencies
    for freq_val_hz in freq_range_hz:

        # set dds frequency
        aq.dds_frequency(dds_name, freq_val_hz)

        # search for amplitude
        for amp_val in amp_range_pct:

            # get calibrated asf
            amp_target_pct = recursion_search(amp_range_pct[0], amp_range_pct[1])

            # tmp remove
            #print('res: {}'.format(amp_target_pct))

            # add to data vault
            dv.add(freq_val_hz, amp_target_pct, context=cr)


except Exception as e:
    print('Error:', e)
