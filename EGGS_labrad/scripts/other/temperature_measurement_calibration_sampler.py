"""
Temperature Measurement Calibration

Calibration sequence to get the relevant amplitude scaling factors for the probe beam for
the temperature measurement experiment.
"""
import labrad
from time import sleep

from numpy import linspace, abs
from EGGS_labrad.clients import createTrunk


# experiment parameters
name_tmp = 'Temperature Measurement Calibration'

# dds parameters
dds_name =                  'urukul1_ch1'
dds_freq_range_hz =         linspace(80, 140, 25) * 1e6
dds_amp_range_pct =         [0, 0.5]
dds_att_db =                14

# sampler parameters
pd_channel_sampler =        5
pd_gain_sampler =           100
pd_sample_rate_hz =         5000
pd_sample_num =             1000

# search parameters
pd_voltage_target_v =       0.035
pd_voltage_tolerance_v =    0.007


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

    # set up sampler channel for photodiode channel
    aq.sampler_gain(pd_channel_sampler, pd_gain_sampler)
    aq.dds_toggle(dds_name, True)
    aq.dds_attenuation(dds_name, dds_att_db)
    print("ARTIQ setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'Temperature Measurement Calibration Sampler',
        [('DDS Frequency', 'Hz')],
        [('DDS Amplitude', 'Amplitude', 'pct')],
        context=cr
    )
    dv.add_parameter("Photodiode Sample Rate", pd_sample_rate_hz, context=cr)
    dv.add_parameter("Photodiode Sample Number", pd_sample_num, context=cr)
    dv.add_parameter("Photodiode Gain", pd_gain_sampler, context=cr)
    dv.add_parameter("Photodiode Target Voltage", pd_voltage_target_v, context=cr)
    dv.add_parameter("Photodiode Target Tolerance", pd_voltage_tolerance_v, context=cr)
    print("Dataset successfully created.")


    # create recursive binary search function
    def recursion_search(amp_min_pct, amp_max_pct):
        # set asf and get power
        amp_tmp_pct = 0.5 * (amp_min_pct + amp_max_pct)
        aq.dds_amplitude(dds_name, amp_tmp_pct)
        sleep(0.5)
        volt_tmp_v = aq.sampler_read([pd_channel_sampler], pd_sample_rate_hz, pd_sample_num)

        # return target value
        if abs(volt_tmp_v - pd_voltage_target_v) <= pd_voltage_tolerance_v:
            return amp_tmp_pct
        elif volt_tmp_v < pd_voltage_target_v:
            return recursion_search(amp_tmp_pct, amp_max_pct)
        else:
            return recursion_search(amp_min_pct, amp_tmp_pct)

    # tmp remove
    res = []

    # sweep frequencies
    for freq_val_hz in dds_freq_range_hz:

        # set dds frequency
        aq.dds_frequency(dds_name, freq_val_hz)

        # get calibrated asf
        amp_target_pct = recursion_search(*dds_amp_range_pct)

        # add to data vault
        dv.add(freq_val_hz, amp_target_pct, context=cr)
        res.append(amp_target_pct)


except Exception as e:
    print('Error:', e)
