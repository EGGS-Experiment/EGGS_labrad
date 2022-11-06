"""
Characterize the low frequency harmonics of the Urukul.
"""
import labrad
from time import sleep
from numpy import arange, linspace, zeros, mean, amax

from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'Urukul Harmonic Characterization'

# dds parameters
dds_channel = 'urukul0_ch2'
dds_amp_pct = 50
dds_att_list_dbm = arange(5, 11)
dds_freq_list_hz = arange(300, 3000) * 1e3

# device parameters
sa_att_db = 0
sa_span_hz = 1000
sa_bandwidth_hz = 100


try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    aq = cxn.artiq_server
    sa = cxn.spectrum_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # check DDS attenuation values are valid
    if amax(dds_att_list_dbm) < 2:
        raise Exception("Error: value in dds attenuation list is too high.")

    # set up DDSs
    aq.dds_toggle(dds_channel, 1)
    aq.dds_amplitude(dds_channel, dds_amp_pct / 100)
    print("ARTIQ DDS setup successful.")

    # set up spectrum analyzer
    sa.select_device()
    sa.attenuation(sa_att_db)
    sa.frequency_span(sa_span_hz)
    sa.bandwidth_resolution(sa_bandwidth_hz)
    sa.marker_toggle(1, True)
    sa.peak_search(True)
    # average readings
    # TODO: set up averaging on device
    print("Spectrum analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Data vault successfully setup.")

    # sweep attenuation
    for att_val in dds_att_list_dbm:

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

        # set attenuation
        aq.dds_attenuation(dds_channel, att_val)

        # sweep frequency
        for freq_val in dds_freq_list_hz:

            # set asf
            aq.dds_amplitude(dds_channel, freq_val)

            # get power of 0th order
            sa.frequency_center(freq_val)
            sleep(1)
            sa.gpib_query('*OPC?')
            zeroth_power = sa.marker_amplitude(1)

            # get power of 1st order harmonic
            sa.frequency_center(2 * freq_val)
            sleep(1)
            sa.gpib_query('*OPC?')
            first_power = sa.marker_amplitude(1)

            # get power of 2nd order harmonic
            sa.frequency_center(3 * freq_val)
            sleep(1)
            sa.gpib_query('*OPC?')
            second_power = sa.marker_amplitude(1)

            # record result
            print("freq {:f}: 0th = {:f}, first = {:f}, second = {:f}".format(freq_val, zeroth_power, first_power, second_power))
            dv.add(freq_val, zeroth_power, first_power, second_power, context=cr)

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
