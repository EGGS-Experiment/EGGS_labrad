"""
Characterize the harmonics of a system.
"""
import labrad
from time import sleep
from numpy import arange, linspace, zeros, mean, amax

from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'Signal Harmonic Characterization'

# function generator parameters
#dds_amp_1_vpp_list = arange(5, 10 + 0.1, 0.1)
rf_amp_1_vpp = 5
rf_freq_1_hz = 19e6

rf_amp_2_vpp_list = arange(0.5, 4, 0.01)
rf_freq_2_list_hz = arange(300, 2000, 5) * 1e3

# device parameters
sa_att_db = 10
sa_span_hz = 5e6
sa_bandwidth_hz = 1e3


# main loop
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    fg = cxn.function_generator_server
    sa = cxn.spectrum_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up function generator
    fg.toggle(1)
    fg.amplitude()
    print("Function generator setup successful.")

    # set up spectrum analyzer
    sa.select_device(1)
    sa.attenuation(sa_att_db)
    sa.frequency_span(sa_span_hz)
    sa.frequency_center(rf_freq_1_hz)
    sa.bandwidth_resolution(sa_bandwidth_hz)
    # set up spectrum analyzer markers
    for i in range(5):
        sa.marker_toggle(i, True)
        sa.marker_mode(i, 0)

    #sa.peak_search(True)
    # average readings
    # TODO: set up averaging on device
    print("Spectrum analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Data vault successfully setup.")

    # wrap readout in error handling to prevent problems
    def _get_pow():
        sa_pow = 0
        try:
            sleep(2)
            sa_pow = sa.marker_amplitude(1)
        except Exception as e:
            print("fehler welp")
            sleep(5)
            sa_pow = sa.marker_amplitude(1)

        return sa_pow

    # sweep attenuation
    for att_val in rf_att_list_dbm:

        # create dataset
        dataset_title_tmp = '{}: {} dB'.format(name_tmp, str(att_val).replace('.', '_'))
        dv.new(
            dataset_title_tmp,
            [('Frequency', 'Hz')],
            [('0th Order Harmonic', 'Power', 'dBm'), ('1st Order Harmonic', 'Power', 'dBm'), ('2nd Order Harmonic', 'Power', 'dBm')],
            context=cr
        )
        dv.add_parameter("attenuation", att_val, context=cr)
        dv.add_parameter("amplitude_fractional", dds_amp_pct, context=cr)

        # sweep frequency
        for freq_val in dds_freq_list_hz:

            # set asf
            fg.dds_frequency(dds_channel, freq_val)

            # get power of 0th order
            sa.frequency_center(freq_val)
            zeroth_power = _get_pow()

            # get power of 1st order harmonic
            sa.frequency_center(2 * freq_val)
            first_power = _get_pow()

            # get power of 2nd order harmonic
            sa.frequency_center(3 * freq_val)
            second_power = _get_pow()

            # record result
            print("freq {:f}: 0th = {:f}, first = {:f}, second = {:f}".format(freq_val, zeroth_power, first_power, second_power))
            dv.add(freq_val, zeroth_power, first_power, second_power, context=cr)

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
