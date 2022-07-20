"""
Record the number of counts while tickling.
"""
# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep, time

from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Tickle PMT Counting'

secular_frequency = 1e6
secular_amplitude = 1
scan_frequencies = linspace(-20, 20, 21)
pmt_ttl = 0


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    fg = cxn.functiongenerator_server
    aq = cxn.artiq_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up oscilloscope
    fg.select_device()
    fg.frequency(secular_frequency)
    fg.amplitude(1)
    fg.toggle(0)
    print('Function generator setup successful.')

    # create dataset
    dv_dep_var = [('{:.f} Detuned Tickle', 'Frequency', 'kHz')
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
    scan_frequencies += secular_frequency
    pmt_counts = zeros(len(scan_frequencies))

    # do timing
    starttime = time()

    while True:
        # tickle and get counts at each detuning
        for i, frequency in enum(scan_frequencies):
            # turn on tickle
            fg.frequency(frequency)
            fg.toggle(1)
            # 100 us, averaged 10 times
            pmt_counts[i] = aq.ttl_counter('ttl_counter0', 100, 10)
            # turn off tickle
            fg.toggle(0)

        # record result
        dv.add([time() - starttime] + pmt_counts, context=cr)
        sleep(3)

except Exception as e:
    print('Error:', e)
