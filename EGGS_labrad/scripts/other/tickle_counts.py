"""
Record the number of counts while tickling.
"""
# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep, time

import numpy as np
from numpy import linspace, zeros
from EGGS_labrad.clients import createTrunk

name_tmp = 'Tickle PMT Counting'

tickle_frequency = 1e6
tickle_amplitude = 1
scan_frequencies = linspace(-10, 10, 21) * 1e3
pmt_ttl, pmt_time_us, pmt_trials = (0, 100, 10)
delay_time_s = 10


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    fg = cxn.function_generator_server
    aq = cxn.artiq_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up oscilloscope
    fg.select_device()
    fg.frequency(tickle_frequency)
    fg.amplitude(tickle_amplitude)
    fg.toggle(0)
    print('Function generator setup successful.')

    # create dataset
    dv_dep_var = [('{:.3f} kHz Detuned Tickle'.format(frequency / 1e3), 'Frequency', 'kHz')
                  for frequency in scan_frequencies]
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'Tickle Counts',
        [('Elapsed time', 't')],
        dv_dep_var,
        context=cr
    )
    print('Dataset successfully created.')


    # scan frequencies
    scan_frequencies += tickle_frequency
    pmt_counts = zeros(len(scan_frequencies))

    # do timing
    starttime = time()

    # main loop
    while True:
        # tickle and get counts at each detuning
        for i, frequency in enumerate(scan_frequencies):
            # turn on tickle
            fg.frequency(frequency)
            fg.toggle(1)
            # 100 us, averaged 10 times
            sleep(0.5)
            #pmt_counts[i] = aq.ttl_counter('ttl_counter{:d}'.format(pmt_ttl), pmt_time_us, pmt_trials)
            pmt_counts[i] = np.random.randint(10)
            # turn off tickle
            fg.toggle(0)
            sleep(0.5)

        # record resultg
        dv.add(np.concatenate(([time() - starttime], pmt_counts)), context=cr)
        sleep(delay_time_s)

except Exception as e:
    print('Error:', e)
