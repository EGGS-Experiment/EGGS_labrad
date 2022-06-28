"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
"""

import labrad
from time import sleep
import numpy as np
from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization'
freq_range = linspace(10, 30, 30 + 1) * 1e6
amp_range = linspace(1, 10, 30)
# todo: set channel


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    os = cxn.oscilloscope_server
    rf = cxn.rf_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up oscilloscope
    os.select_device()
    # todo: set up channel?
    # todo: set up measurement properly

    # set up signal generator
    rf.select_device()
    rf.gpib_write("AM OFF")
    print('Device setup successful.')

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print('Dataset successfully created')

    for freq_val in freq_range:
        # set signal frequency
        rf.frequency(freq_val)

        # create dataset
        dv.new(
            'Rectifier Response {:f} MHz'.format(freq_val / 1e6),
            [('RF Amplitude', 'dBm')],
            [('Rectifier Offset', 'DC Offset', 'V'), ('Rectifier Value', 'Oscillation Amplitude', 'V')],
            context = cr
        )

        for amp_val in amp_range:
            # set signal amplitude
            rf.amplitude(amp_val)
            sleep(2)

            # todo: better way of waiting for autoscale/setting channel scale
            # autoscale first
            os.autoscale()
            sleep(7)

            # set offset to mean value
            offset_val = os.gpib_query('MEASU:MEAS4:VAL?')
            os.channel_offset(3, offset_val)

            # zoom in on oscillation
            osc_val = os.gpib_query('MEASU:MEAS3:VAL?')
            osc_val = float(osc_val) / 2
            if osc_val == 0:
                osc_val = 5e-3
            os.channel_scale(3, osc_val)
            sleep(2)

            # take oscope data
            offset_val = os.gpib_query('MEASU:MEAS4:VAL?')
            osc_val = os.gpib_query('MEASU:MEAS3:VAL?')
            print('freq: {}; amp: {}; offset: {}; osc: {}'.format(freq_val, amp_val, float(offset_val), float(osc_val)))

            # record result
            dv.add(amp_val, offset_val, osc_val, context=cr)

except Exception as e:
    print('Error:', e)
