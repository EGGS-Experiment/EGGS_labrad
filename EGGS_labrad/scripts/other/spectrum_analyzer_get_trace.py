"""
Measure values from a spectrum analyzer.
"""
import labrad
from time import time, sleep
from datetime import datetime

import numpy
from numpy import arange, linspace, zeros, mean, amax


from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'spectrum_analyzer_trace'

# polling parameters
poll_delay_s =          60

# spectrum analyzer parameters
sa_device_num_dj =      0
sa_att_int_db =         10
sa_att_ext_db =         20
sa_span_hz =            1000000
sa_bandwidth_hz =       1000

# todo: do variable number of peaks


# main loop
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    sa = cxn.spectrum_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up spectrum analyzer
    sa.select_device(sa_device_num_dj)
    sa.attenuation(sa_att_int_db)
    sa.frequency_span(sa_span_hz)
    sa.bandwidth_resolution(sa_bandwidth_hz)
    sa.marker_toggle(1, True)
    print("Spectrum analyzer setup successful.")
    num_points=len(sa.trace(1)[1])

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dataset_title_tmp = 'spectrum_analyzer_trace'

    independents = [('Elapsed Time', [1], 'v', 's')]
    dependents = [
        ('Signal Frequency',    'Frequency',    [num_points],   'v',    'Hz'),
        ('Signal Power',        'Power',        [num_points],   'v',    'dBm')
    ]
    dv.new_ex(dataset_title_tmp, independents, dependents, context=cr)

    dv.add_parameter("spectrum_analyzer_bandwidth",                 sa_bandwidth_hz,    context=cr)
    dv.add_parameter("spectrum_analyzer_attenuation_internal",      sa_att_int_db,      context=cr)
    dv.add_parameter("spectrum_analyzer_attenuation_external",      sa_att_ext_db,      context=cr)
    print("Data vault setup successful.")


    # MAIN LOOP
    starttime = time()
    #while True:
    for x in range(1, 900, 1):

        try:
            # get signal values
            sa_freq_hz = sa.marker_frequency(1)
            sa_pow_dbm = sa.marker_amplitude(1)

            sa_trace =  sa.trace(1)
            freq =      sa_trace[0].transpose()
            amp =       sa_trace[1].transpose()

            # record data into data vault
            elapsedtime = time() - starttime
            #dv.add(elapsedtime, sa_trace[0][numpy.argmax(sa_trace[1])], max(sa_trace[1]), context=cr)
            dv.add_ex([(elapsedtime, freq, amp)], context=cr)
            #dv.add(elapsedtime, sa_freq_hz, sa_pow_dbm, context=cr)

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
