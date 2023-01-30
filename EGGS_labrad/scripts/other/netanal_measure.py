"""
Measure values from a network analyzer.
"""
import labrad
from time import time, sleep
from datetime import datetime
from numpy import arange, linspace, zeros, mean, amax


from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'Network Analyzer Measurement'

# polling parameters
poll_delay_s =          1.0

# network analyzer parameters
na_device_num_dj =      3
na_att_int_db =         10
na_att_ext_db =         11.5
na_span_hz =            100
na_bandwidth_hz =       10

# todo: do variable number of peaks


# main loop
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    na = cxn.network_analyzer_server
    tec = cxn.amo2_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up network analyzer
    na.select_device()
    #na.marker_toggle(1, True)
    #na.gpib_write('CALC1:MARK:FUNC MIN')
    #na.gpib_write('CALC1:MARK:FUNC:TRAC ON')


    # na.select_device(na_device_num_dj)
    # na.attenuation(na_att_int_db)
    # na.frequency_span(na_span_hz)
    # na.bandwidth_resolution(na_bandwidth_hz)
    # na.marker_toggle(1, True)
    print("Network analyzer setup successful.")

    # set up amo2 server
    # todo

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dataset_title_tmp = 'Network Analyzer Measurement'
    dv.new(
        dataset_title_tmp,
        [('Time', 's')],
        [
            ('Resonator Temperature',   'Temperature',      'C'),
            ('Resonance Power',         'Transmission',     'dB'),
            ('Resonance Frequency',     'Frequency',        'Hz'),
            ('Left Bandwidth',          'Frequency',        'Hz'),
            ('Right Bandwidth',         'Frequency',        'Hz')
        ],
        context=cr
    )
    # dv.add_parameter("network_analyzer_bandwidth",                 na_bandwidth_hz,    context=cr)
    # dv.add_parameter("network_analyzer_attenuation_internal",      na_att_int_db,      context=cr)
    # dv.add_parameter("network_analyzer_attenuation_external",      na_att_ext_db,      context=cr)
    print("Data vault setup successful.")


    # MAIN LOOP
    starttime = time()
    while True:

        try:
            # get signal values
            na_res_pow_db = float(na.gpib_query('CALC:MARK1:Y?'))
            na_res_freq_hz = float(na.gpib_query('CALC:MARK1:X?'))
            na_left_bw_freq_hz = float(na.gpib_query('CALC:MARK2:X?'))
            na_right_bw_freq_hz = float(na.gpib_query('CALC:MARK3:X?'))

            # record data into data vault
            elapsedtime = time() - starttime
            dv.add(elapsedtime, na_res_pow_db, na_res_freq_hz, na_left_bw_freq_hz, na_right_bw_freq_hz, context=cr)

        except Exception as e:
            # log time and error description
            error_time = datetime.now()
            print("{}::\tError: {}".format(error_time.strftime("%m/%d/%Y, %H:%M:%S"), e))

        finally:

            # wait given time
            sleep(poll_delay_s)

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
