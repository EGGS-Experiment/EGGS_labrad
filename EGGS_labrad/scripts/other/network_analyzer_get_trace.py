"""
Measure values from a network analyzer.
"""
import labrad
from time import time, sleep
from datetime import datetime

import numpy
from numpy import arange, linspace, zeros, mean, amax


from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'network_analyzer_trace'

# polling parameters
poll_delay_s =          60

# network analyzer parameters
na_device_num_dj =      0
na_att_int_db =         10
na_att_ext_db =         20
na_span_hz =            1000000
na_bandwidth_hz =       1000

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
    na.select_device(na_device_num_dj)
    # na.attenuation(na_att_int_db)
    # na.frequency_span(na_span_hz)
    # na.bandwidth_resolution(na_bandwidth_hz)
    # na.marker_toggle(1, True)
    print("Network analyzer setup successful.")
    num_points=len(na.trace_acquire(1)[1])

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dataset_title_tmp = 'network_analyzer_trace'

    independents = [('Elapsed Time', [1], 'v', 's')]
    dependents = [
        ('Signal Frequency', 'Frequency', [num_points],'v', 'Hz'),
        ('Signal Power', 'Power', [num_points], 'v', 'dBm')
        ('Notch ', 'Power', [num_points], 'v', 'dBm')
    ]
    dv.new_ex(dataset_title_tmp, independents, dependents, context=cr)

    # dv.add_parameter("network_analyzer_bandwidth",                  na_bandwidth_hz,    context=cr)
    # dv.add_parameter("network_analyzer_attenuation_internal",       na_att_int_db,      context=cr)
    # dv.add_parameter("network_analyzer_attenuation_external",       na_att_ext_db,      context=cr)
    print("Data vault setup successful.")


    # MAIN LOOP
    starttime = time()
    #while True:
    for x in range(1,900,1):

        try:
            # get signal values
            na_freq_hz = na.marker_frequency(1)
            na_pow_dbm = na.marker_amplitude(1)

            na_trace=na.trace_acquire(1)
            freq = na_trace[0].transpose()
            amp = na_trace[1].transpose()

            # record data into data vault
            elapsedtime = time() - starttime
            #dv.add(elapsedtime, na_trace[0][numpy.argmax(na_trace[1])], max(na_trace[1]), context=cr)
            dv.add_ex([(elapsedtime, freq, amp)], context=cr)
            #dv.add(elapsedtime, na_freq_hz, na_pow_dbm, context=cr)

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
