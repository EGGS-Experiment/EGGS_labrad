"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
Uses the ARTIQ Sampler.
"""

# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep

from numpy import linspace, mean, std
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization'
freq_range = linspace(19.013, 19.033, 21) * 1e6
amp_range = linspace(-22, -15, 71)

sampler_channel = 0
sample_num = 100
sample_rate = 100

try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    aq = cxn.artiq_server
    rf = cxn.rf_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up sampler
    aq.sampler_gain(1, 10)
    print("Sampler setup successful.")

    # set up signal generator
    rf.select_device()
    rf.gpib_write("AM OFF")
    rf.toggle(1)
    print("Signal generator setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Dataset successfully created.")

    # sweep frequencies
    for freq_val in freq_range:

        # set signal frequency
        rf.frequency(freq_val)

        # create dataset
        dv.new(
            'Rectifier Response {:d} kHz'.format(int(freq_val / 1e3)),
            [('RF Amplitude', 'dBm')],
            [('Rectifier Offset', 'DC Offset', 'V'), ('Rectifier Value', 'Oscillation Amplitude', 'V')],
            context=cr
        )
        dv.add_parameter("Frequency", freq_val, context=cr)

        # sweep amplitudes
        for amp_val in amp_range:

            # set amplitude
            rf.amplitude(amp_val)

            # take sampler data
            rectifier_output = aq.sampler_read_list([sampler_channel], sample_rate, sample_num) * 2
            print(mean(rectifier_output))
            dv.add(amp_val, mean(rectifier_output), std(rectifier_output), context=cr)

except Exception as e:
    print('Error:', e)
