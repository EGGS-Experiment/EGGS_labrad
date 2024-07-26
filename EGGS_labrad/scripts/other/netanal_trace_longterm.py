"""
Measure values over a long term from a network analyzer.
"""
import labrad
from time import time, time_ns, sleep
from datetime import datetime

from EGGS_labrad.clients import createTrunk

# # tmp remove
# import logging
# logger = logging.getLogger('my_module_name')


# experiment parameters
name_tmp = 'network_analyzer_trace_longterm'

# polling parameters
poll_delay_s =          1.5
record_trace_num =      5000
# network analyzer parameters
na_device_num_dj =      8
# na_att_int_db =         10
# na_att_ext_db =         20
# na_span_hz =            1000000
# na_bandwidth_hz =       1000


# main loop
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    # na = cxn.network_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up network analyzer
    # na.select_device(na_device_num_dj)
    # na.attenuation(na_att_int_db)
    # na.frequency_span(na_span_hz)
    # na.bandwidth_resolution(na_bandwidth_hz)
    # na.marker_toggle(1, True)
    # print("Network analyzer setup successful.")

    # do pyvisa by ourselves
    import pyvisa
    # instantiate and alias objects
    rm =    pyvisa.ResourceManager()
    rmor =  rm.open_resource
    lr =    rm.list_resources()
    # get devices
    na =    rmor(lr[na_device_num_dj])

    # get trace parameters
    num_points = na.query('SENS:SWE:POIN?')
    num_points = int(num_points.strip())

    sweep_time_s = na.query('SENS:SWE:TIME?')
    sweep_time_s = float(sweep_time_s.strip())

    pow_rf_dbm = na.query('SOUR:POW?')
    pow_rf_db = float(pow_rf_dbm.strip())

    freq_start_hz = na.query('SENS:FREQ:STAR?')
    freq_start_hz = float(freq_start_hz.strip())

    freq_stop_hz = na.query('SENS:FREQ:STOP?')
    freq_stop_hz = float(freq_stop_hz.strip())

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dataset_title_tmp = 'network_analyzer_longterm'

    independents = [('Elapsed Time', [1], 'v', 's')]
    dependents = [
        ('Insertion Loss',  'Power',        [num_points],   'v',    'dB'),
        ('Phase Delay',     'Phase',        [num_points],   'v',    'deg')
    ]
    dv.new_ex(dataset_title_tmp, independents, dependents, context=cr)

    dv.add_parameter("network_analyzer_power",              pow_rf_dbm,     context=cr)
    dv.add_parameter("network_analyzer_sweep_time_s",       sweep_time_s,   context=cr)

    dv.add_parameter("network_analyzer_points",             num_points,     context=cr)
    dv.add_parameter("network_analyzer_freq_start_hz",      freq_start_hz,   context=cr)
    dv.add_parameter("network_analyzer_freq_stop_hz",       freq_stop_hz,   context=cr)
    print("Data vault setup successful.")


    # MAIN LOOP
    starttime = time()
    for _iter in range(record_trace_num):

        try:
            # get & process trace 1
            time_calc1_start =  time_ns()
            trace_raw_meas1 =   na.query('CALC1:DATA?')
            time_calc1_run =    time_ns() - time_calc1_start
            trace_data_meas1 =  [float(val) for val in trace_raw_meas1.strip().split(',')]
            # print('\tRound {:d}: CALC1 - OK\n\t\tTime (ms): {:.3f}\n\t\tVal: {:f}'.format(_iter, time_calc1_run / 1e6, trace_data_meas1[0]))
            sleep(poll_delay_s)

            # get & process trace 2
            time_calc2_start =  time_ns()
            trace_raw_meas2 =   na.query('CALC2:DATA?')
            time_calc2_run =    time_ns() - time_calc2_start
            trace_data_meas2 =  [float(val) for val in trace_raw_meas2.strip().split(',')]
            # print('\tRound {:d}: CALC2 - OK\n\t\tTime (ms): {:.3f}\n\t\tVal: {:f}'.format(_iter, time_calc2_run / 1e6, trace_data_meas2[0]))


            # save data to datavault
            elapsedtime = time() - starttime
            dv.add_ex([(elapsedtime, trace_data_meas1, trace_data_meas2)], context=cr)
            # dv.add(elapsedtime, na_trace[0][numpy.argmax(na_trace[1])], max(na_trace[1]), context=cr)
            # dv.add(elapsedtime, na_freq_hz, na_pow_dbm, context=cr)

        except Exception as e:
            # log time and error description
            error_time = datetime.now()
            print("{}::\tError: {}".format(error_time.strftime("%m/%d/%Y, %H:%M:%S"), e))

        finally:
            # wait given time
            sleep(poll_delay_s)


except Exception as e:
    print("Error:", e)
    # cxn.disconnect()

