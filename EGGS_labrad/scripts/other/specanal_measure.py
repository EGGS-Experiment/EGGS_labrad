"""
Measure values from a spectrum analyzer.
"""
import labrad
from time import time, sleep
from datetime import datetime
from numpy import array, arange, linspace, zeros, mean, amax


from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp =              'Spectrum Analyzer Measurement'

# polling parameters
poll_delay_s =          5.0
record_time_s =         1000

# spectrum analyzer parameters
sa_device_num_dj =      0
sa_att_int_db =         0
sa_att_ext_db =         0
sa_span_hz =            400
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
    # sa.attenuation(sa_att_int_db)
    # sa.frequency_span(sa_span_hz)
    # sa.bandwidth_resolution(sa_bandwidth_hz)
    # sa.marker_toggle(1, True)
    sa.gpib_write('DISP:ENAB 0')
    print("Spectrum analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dataset_title_tmp = 'Spectrum Analyzer Measurement'
    dv.new(
        dataset_title_tmp,
        [('Time', 's')],
        [
            ('Signal Frequency',    'Frequency',    'Hz'),
            ('Signal Power',        'Power',        'dBm')
        ],
        context=cr
    )
    dv.add_parameter("spectrum_analyzer_bandwidth",                 sa_bandwidth_hz,    context=cr)
    dv.add_parameter("spectrum_analyzer_attenuation_internal",      sa_att_int_db,      context=cr)
    dv.add_parameter("spectrum_analyzer_attenuation_external",      sa_att_ext_db,      context=cr)
    print("Data vault setup successful.")


    # MAIN LOOP
    starttime = time()
    elapsedtime = 0
    while elapsedtime < record_time_s:

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

    # re-enable display
    sa.gpib_write('DISP:ENAB 1')

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
