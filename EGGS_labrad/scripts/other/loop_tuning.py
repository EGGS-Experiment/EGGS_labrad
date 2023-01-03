"""
Tune the AMO2 box by adjusting its PID locking parameters and reading the output
on an oscilloscope.
"""
# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep

from numpy import linspace, arange, array
from EGGS_labrad.clients import createTrunk


# PARAMETERS
name_tmp = 'Loop Tuning'

lock_setpoint = 23.5
lock_p_range = arange(255)
lock_i_range = arange(255)

os_signal_channel = 3
os_measure_slots = (3, 4)
os_measure_time_s = 50
os_delay_time_s = 50


# MAIN LOOP
try:

    # SETUP

    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    os = cxn.oscilloscope_server
    pid = cxn.amo2_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up PID controller
    pid.toggle(0)
    pid.locking_setpoint(lock_setpoint)
    pid.locking_p(0)
    pid.locking_i(0)
    pid.locking_d(0)
    print("PID setup successful.")

    # set up oscilloscope
    os.select_device()
    os.measure_setup(os_measure_slots[0], os_signal_channel, 'RMS')
    os.measure_setup(os_measure_slots[1], os_signal_channel, 'MEAN')
    os.trigger_channel(os_signal_channel)
    print("Oscilloscope setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'Loop Tuning',
        [('Proportional', 'Dimensionless')],
        [
            ('Error Mean', 'Mean', 'V'),
            ('Error RMS', 'RMS', 'V')
        ],
        context=cr
    )
    # todo: store current time
    dv.add_parameter("Locking Setpoint", lock_setpoint, context=cr)
    print("Dataset successfully created")


    # MAIN SEQUENCE

    # activate PID lock
    pid.toggle(1)
    sleep(10)

    # center around error signal
    os.autoscale()
    sleep(10)
    os.horizontal_scale(os_measure_time_s / 10)

    # sweep locking parameter
    for p_val in lock_p_range:

        # set parameter value
        pid.locking_p(p_val)

        # wait for signal to stabilize
        sleep(os_delay_time_s)

        # wait for signal to take up whole screen
        sleep(os_measure_time_s)

        # record oscope data
        mean_val = os.measure(os_measure_slots[0])
        rms_val = os.measure(os_measure_slots[1])

        # record result
        dv.add(p_val, mean_val, rms_val, context=cr)

except Exception as e:
    print('Error: {}'.format(e))
