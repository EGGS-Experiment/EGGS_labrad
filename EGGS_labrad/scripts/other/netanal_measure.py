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
poll_delay_s =          0.75

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
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up network analyzer
    na.select_device()
    na.marker_toggle(1, True)
    na.gpib_write('CALC1:MARK:FUNC MIN')
    na.gpib_write('CALC1:MARK:FUNC:TRAC ON')
    # na.select_device(na_device_num_dj)
    # na.attenuation(na_att_int_db)
    # na.frequency_span(na_span_hz)
    # na.bandwidth_resolution(na_bandwidth_hz)
    # na.marker_toggle(1, True)
    # print("Network analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dataset_title_tmp = 'Network Analyzer Measurement'
    dv.new(
        dataset_title_tmp,
        [('Time', 's')],
        [
            ('Resonance Frequency',    'Frequency',    'Hz'),
            ('Resonance Power',        'Transmission',  'dB')
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
            sa_freq_hz = sa.marker_frequency(1)
            sa_pow_dbm = sa.marker_amplitude(1)

            # record data into data vault
            elapsedtime = time() - starttime
            dv.add(elapsedtime, sa_freq_hz, sa_pow_dbm, context=cr)

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
