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
na_device_num_dj =      0
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
    # tec = cxn.amo2_server
    ls = cxn.lakeshore336_server
    na = cxn.network_analyzer_server
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
            # network analyzer values
            ('Resonator Bandwidth',     'Frequency',        'Hz'),
            ('Resonance Frequency',     'Frequency',        'Hz'),
            ('Resonator Q',             'Gain',             'idk'),
            ('Resonator Loss',          'Gain',             'dB'),

            # temperature values
            ('Diode 1', 'Temperature', 'K'),
            ('Diode 2', 'Temperature', 'K'),
            ('Diode 3', 'Temperature', 'K'),
            ('Diode 4', 'Temperature', 'K')
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
            # tec_res_temp_c = tec.temperature()
            # na_res_pow_db = float(na.gpib_query('CALC:MARK1:Y?'))
            # na_res_freq_hz = float(na.gpib_query('CALC:MARK1:X?'))
            #na_left_bw_freq_hz = float(na.gpib_query('CALC:MARK2:X?'))
            #na_right_bw_freq_hz = float(na.gpib_query('CALC:MARK3:X?'))
            na_notch_vals = [float(val) for val in na.gpib_query('CALC:MARK:FUNC:RES?').split(',')]
            ls_temp_vals = ls.read_temperature()

            # record data into data vault
            elapsedtime = time() - starttime
            dv.add(elapsedtime, *na_notch_vals, *ls_temp_vals, context=cr)
            #dv.add(elapsedtime, tec_res_temp_c, na_res_pow_db, na_res_freq_hz, na_left_bw_freq_hz, na_right_bw_freq_hz, context=cr)

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
