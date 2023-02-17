"""


Attempt to tune the frequency of the trap RF to the can resonance.
"""

# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep
from random import shuffle

from numpy import linspace, mean, std
from EGGS_labrad.clients import createTrunk

name_tmp = 'Resonance Tune'
freq_range_hz = linspace(19.044, 19.045, 400) * 1e6
shuffle(freq_range_hz)

sampler_channel_num =       0
sampler_gain =              1000
sampler_sample_num =        10000
sampler_sample_rate_hz =    1000


# MAIN LOOP
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
    aq.sampler_gain(sampler_channel_num, sampler_gain)
    print("Sampler setup successful.")

    # set up signal generator
    rf.select_device()
    # todo: slowly ramp down locking
    # rf.gpib_write("AM OFF")
    rf.toggle(1)
    print("Signal generator setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'Resonator Resonance Tune {:d}',
        [('RF Frequency', 'Hz')],
        [
            ('Sampler Error Mean',      'Error Signal',         'V'),
            ('Sampler Error Stdev',     'Standard Deviation',   'V')
        ],
        context=cr
    )
    dv.add_parameter("sampler_gain",            sampler_gain,           context=cr)
    dv.add_parameter("sampler_sample_rate_hz",  sampler_sample_rate_hz, context=cr)
    #dv.add_parameter("sampler_sample_rate_hz", sampler_sample_rate_hz, context=cr)
    # todo: record rf ampl, dac via sampler
    print("Dataset successfully created.")

    # sweep frequencies
    for freq_val_hz in freq_range_hz:

        # set signal frequency
        rf.frequency(freq_val_hz)
        sleep(0.1)

        # take sampler data
        rectifier_output = aq.sampler_read_list([sampler_channel_num], sampler_sample_rate_hz, sampler_sample_num)
        dv.add(freq_val_hz, mean(rectifier_output), std(rectifier_output), context=cr)

except Exception as e:
    print('Error:', e)
