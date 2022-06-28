"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
"""

import labrad
from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization'
freq_range = linspace()
amp_range = linspace()

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
    # todo: set up measurement
    print('RGA setup successful.')

    # set up signal generator
    rf.select_device()
    rf.gpib_write("AM OFF")

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

            # autoset and wait to adjust


            # take oscope data
            offset_val = os.gpib_query('MEASU:MEAS3:VAL?')
            osc_val = os.gpib_query('MEASU:MEAS4:VAL?')

            # record result
            dv.add(amp_val, offset_val, osc_val, context=cr)

except Exception as e:
    print('Error:', e)
