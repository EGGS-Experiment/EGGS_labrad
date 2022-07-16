"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
"""
# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep, time

from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Pickoff Measurement'
os_channel = 3


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    os = cxn.oscilloscope_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up oscilloscope
    os.select_device()
    #os.measure_setup(3, os_channel, 'MEAN')
    #os.trigger_channel(os_channel)
    # os.trigger_level
    print('Oscilloscope setup successful.')

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print('Dataset successfully created')

    # create dataset
    dv.new(
        'Pickoff Measurement',
        [('Time', 's')],
        [('Rectifier Output', 'V_amplitude', 'V'), ('Signal Max', 'Voltage', 'V')],
        context=cr
    )

    # do timing
    starttime = time()

    while True:
        # first zoom out
        # os.channel_offset(os_channel, 0)
        # os.channel_scale(os_channel, 1)
        # sleep(1)

        # # center around offset
        # offset_val = os.measure(4)
        # os.channel_offset(3, offset_val)
        # sleep(0.5)

        # # zoom in on oscillation
        # osc_val = float(os.measure(3)) / 4
        # if osc_val < 5e-3:
        #     osc_val = 5e-3
        # os.channel_scale(3, osc_val)
        # sleep(0.5)
        #
        # # adjust offset again
        # offset_val = os.measure(4)
        # os.channel_offset(3, offset_val)
        # sleep(0.5)
        #
        # # zoom in on oscillation again
        # osc_val = float(os.measure(3)) / 4
        # if osc_val < 5e-3:
        #     osc_val = 5e-3
        # os.channel_scale(3, osc_val)
        # sleep(1)

        # take oscope data
        off_val = os.measure(2)
        max_val = os.measure(1)

        # record result
        dv.add(time() - starttime, off_val, max_val, context=cr)
        sleep(3)

except Exception as e:
    print('Error:', e)
