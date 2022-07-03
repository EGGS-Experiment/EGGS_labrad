"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
"""

import labrad
from time import sleep

from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization'
freq_range = linspace(10, 30, 30 + 1) * 1e6
amp_range = linspace(1, 10, 30)
os_channel = 3


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
    os.autoscale()
    os.measure_setup(3, os_channel, 'AMP')
    os.measure_setup(4, os_channel, 'MEAN')
    # todo: set up trigger correctly
    # os.trigger_source
    # os.trigger_level
    print('Oscilloscope setup successful.')

    # set up signal generator
    rf.select_device()
    rf.gpib_write("AM OFF")
    print('Signal generator setup successful.')

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print('Dataset successfully created')

    for freq_val in freq_range:
        # set signal frequency
        rf.frequency(freq_val)

        # todo: correctly set timescale

        # create dataset
        dv.new(
            'Rectifier Response {:f} MHz'.format(freq_val / 1e6),
            [('RF Amplitude', 'dBm')],
            [('Rectifier Offset', 'DC Offset', 'V'), ('Rectifier Value', 'Oscillation Amplitude', 'V')],
            context=cr
        )

        for amp_val in amp_range:
            # set signal amplitude
            rf.amplitude(amp_val)

            # first zoom out
            os.channel_offset(os_channel, 0)
            os.channel_scale(os_channel, 1)

            # center around offset
            offset_val = os.measure(4)
            os.channel_offset(3, offset_val)

            # zoom in on oscillation
            osc_val = float(os.measure(3)) / 4
            if osc_val < 5e-3:
                osc_val = 5e-3
            os.channel_scale(3, osc_val)

            # adjust offset again
            offset_val = os.measure(4)
            os.channel_offset(3, offset_val)

            # zoom in on oscillation again
            osc_val = float(os.measure(3)) / 4
            if osc_val < 5e-3:
                osc_val = 5e-3
            os.channel_scale(3, osc_val)

            # take oscope data
            osc_val = os.measure(3)
            offset_val = os.measure(4)
            print('freq: {}; amp: {}; offset: {}; osc: {}'.format(freq_val, amp_val, float(offset_val), float(osc_val)))

            # record result
            dv.add(amp_val, offset_val, osc_val, context=cr)

except Exception as e:
    print('Error:', e)
