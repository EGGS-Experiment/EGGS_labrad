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
rf_amp_1_vpp = 2
rf_freq_1_hz = 19e6

rf_amp_2_vpp_list = arange(0.5, 2, 0.1)
rf_freq_2_list_hz = arange(300, 2000, 1) * 1e3

# device parameters
sa_att_db = 10
sa_span_hz = 5e6
sa_bandwidth_hz = 1e4
sa_num_markers = 5


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
    fg.select_device(1)
    fg.channel(1)
    fg.toggle(1)
    fg.amplitude(rf_amp_1_vpp)
    fg.frequency(rf_freq_1_hz)
    fg.channel(2)
    print("Function generator setup successful.")

    # set up spectrum analyzer
    sa.select_device(1)
    sa.attenuation(sa_att_db)
    sa.frequency_span(sa_span_hz)
    sa.frequency_center(rf_freq_1_hz)
    sa.bandwidth_resolution(sa_bandwidth_hz)
    # set up spectrum analyzer markers
    for i in range(1, sa_num_markers + 1):
        sa.marker_toggle(i, True)
        sa.marker_mode(i, 0)
        sa.marker_trace(i, 1)
    print("Spectrum analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Data vault successfully setup.")

    # wrap readout in error handling to prevent problems
    def _get_pow(channel):
        sa_pow = 0
        try:
            sa_pow = sa.marker_amplitude(channel)
        except Exception as e:
            print("fehler welp")
            sleep(2)
            sa_pow = sa.marker_amplitude(channel)

        return sa_pow


    # MAIN LOOP
    # sweep frequency
    for freq_val_hz in rf_freq_2_list_hz:

        # create dataset
        dataset_title_tmp = '{}: {} kHz'.format(name_tmp, str(freq_val_hz / 1e3).replace('.', '_'))
        dv.new(
            dataset_title_tmp,
            [('Amplitude', 'Vpp')],
            [
                ('1st Order Harmonic', 'Power', 'dBm'),
                ('2nd Order Harmonic (Left)', 'Power', 'dBm'), ('2nd Order Harmonic (Right)', 'Power', 'dBm'),
                ('3rd Order Harmonic (Left)', 'Power', 'dBm'), ('3rd Order Harmonic (Right)', 'Power', 'dBm')
            ],
            context=cr
        )
        dv.add_parameter("carrier_frequency_hz", rf_freq_1_hz, context=cr)
        dv.add_parameter("carrier_amplitude_vpp", rf_amp_1_vpp, context=cr)
        dv.add_parameter("modulation_frequency_hz", freq_val_hz, context=cr)

        # set frequency
        fg.gpib_write('FREQ:CH2 {:f}'.format(freq_val_hz))
        sleep(1)
        #fg.frequency(freq_val_hz)

        # get peaks
        for i in range(1, sa_num_markers + 1):
            # set marker at peak
            sa.peak_set(i)
            sleep(0.5)

            # move ith marker to ith peak
            for j in range(i - 1):
                sa.peak_next(i)
                sleep(0.5)

        # sweep modulation amplitude
        for amp_val_vpp in rf_amp_2_vpp_list:

            # set amplitude
            # try:
            #     fg.channel(2)
            #     fg.amplitude(amp_val_vpp)
            # except Exception as e:
            fg.gpib_write('VOLT:CH2 {}'.format(amp_val_vpp))
            sleep(1)

            # results holder
            res_list = []

            # get marker values
            for i in range(1, sa_num_markers + 1):
                res_list.append(_get_pow(i))

            # record result
            print("amp {:f}: 0th = {:f}, first = {:f}, second = {:f}".format(amp_val_vpp, res_list[0], res_list[1], res_list[3]))
            dv.add([amp_val_vpp] + res_list, context=cr)

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
