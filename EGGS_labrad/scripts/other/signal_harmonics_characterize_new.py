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
rf_amp_1_vpp = 2.4000
rf_freq_1_hz = 19.054 * 1e6

rf_amp_2_vpp_list = arange(0.5, 5.0, 0.1)
rf_freq_2_list_hz = arange(300, 2000, 10) * 1e3

# device parameters
sa_att_int_db = 10
sa_att_ext_db = 30
sa_bandwidth_hz = 25000


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
    fg.select_device(2)
    #fg.channel(1)
    # fg.toggle(1)
    # fg.amplitude(rf_amp_1_vpp)
    # fg.frequency(rf_freq_1_hz)
    # fg.channel(1)
    fg.gpib_write('VOLT:CH2 {}'.format(rf_amp_1_vpp))
    fg.gpib_write('FREQ:CH2 {}'.format(rf_freq_1_hz))
    print("Function generator setup successful.")

    # set up spectrum analyzer
    sa.select_device(3)
    sa.attenuation(sa_att_int_db)
    sa.bandwidth_resolution(sa_bandwidth_hz)
    # tmp remove
    sa.gpib_write('CALC:MARK:PEAK:TABL:STAT 1')
    sa.gpib_write('CALC:MARK:PEAK:SORT AMPL')
    sa.gpib_write('CALC:MARK:PEAK:TABL:READ GTDL')
    print("Spectrum analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Data vault setup successful.")

    # MAIN LOOP
    # sweep frequency
    for amp_val_vpp in rf_amp_2_vpp_list:

        print('starting amp: {}'.format(amp_val_vpp))

        # create dataset
        dataset_title_tmp = '{}: {} Vpp'.format(name_tmp, str(amp_val_vpp / 1e3).replace('.', '_'))
        dv.new(
            dataset_title_tmp,
            [('Modulation Amplitude', 'Vpp')],
            [
                ('1st Order Harmonic', 'Power', 'dBm'),
                ('2nd Order Harmonic (Left)', 'Power', 'dBm'), ('2nd Order Harmonic (Right)', 'Power', 'dBm')#,
                #('3rd Order Harmonic (Left)', 'Power', 'dBm'), ('3rd Order Harmonic (Right)', 'Power', 'dBm')
            ],
            context=cr
        )
        dv.add_parameter("carrier_frequency_hz", rf_freq_1_hz, context=cr)
        dv.add_parameter("carrier_amplitude_vpp", rf_amp_1_vpp, context=cr)
        dv.add_parameter("modulation_amplitude_vpp", amp_val_vpp, context=cr)
        dv.add_parameter("spectrum_analyzer_bandwidth", sa_bandwidth_hz, context=cr)
        dv.add_parameter("spectrum_analyzer_attenuation_internal", sa_att_int_db, context=cr)
        dv.add_parameter("spectrum_analyzer_attenuation_external", sa_att_ext_db, context=cr)

        # set amplitude
        fg.gpib_write('VOLT {}'.format(amp_val_vpp))

        # sweep modulation frequency
        for freq_val_hz in rf_freq_2_list_hz:

            # set frequency
            fg.gpib_write('FREQ {}'.format(freq_val_hz))
            sleep(0.5)

            # get peaks
            resp = sa.gpib_query('CALC:DATA1:PEAK? -80, 10, AMPL, GTDL')

            # parse peaks
            res_list = [float(val) for val in resp.split(',')]
            res_list[0] = int(res_list[0])
            #freq_list = res_list[2::2]
            amp_list = res_list[1::2]
            amp_list = [amp_val_db + sa_att_ext_db for amp_val_db in amp_list]

            # ensure correct number of peaks
            if len(amp_list) > 3:
                amp_list = amp_list[:3]
            elif len(amp_list) < 3:
                amp_list = [0.0, 0.0, 0.0]

            # record result
            dv.add([freq_val_hz] + amp_list, context=cr)

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
