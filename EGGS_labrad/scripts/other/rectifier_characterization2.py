"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
"""
# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep

from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization 2'
freq_range = linspace(18, 23, 500 + 1) * 1e6
amp_val = -40
os_channel = 1


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
    os.measure_setup(3, os_channel, 'AMP')
    os.measure_setup(1, os_channel, 'MEAN')
    os.trigger_channel(os_channel)
    # os.trigger_level
    print('Oscilloscope setup successful.')

    # set up signal generator
    rf.select_device()
    rf.gpib_write("AM OFF")
    rf.amplitude(amp_val)
    print('Signal generator setup successful.')

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'Rectifier Response 2 {:f} dBm'.format(amp_val / 1e6),
        [('Frequency', 'MHz')],
        [('Rectifier Offset', 'DC Offset', 'V'), ('Rectifier Value', 'Oscillation Amplitude', 'V')],
        context=cr
    )
    print('Dataset successfully created')

    for freq_val in freq_range:
        # set signal frequency
        rf.frequency(freq_val)

        # first zoom out
        os.channel_offset(os_channel, 0)
        os.channel_scale(os_channel, 1)
        sleep(1)

        # center around offset
        offset_val = os.measure(1)
        os.channel_offset(3, offset_val)
        sleep(0.5)

        # zoom in on oscillation
        osc_val = float(os.measure(3)) / 4
        if osc_val < 5e-3:
            osc_val = 5e-3
        os.channel_scale(3, osc_val)
        sleep(0.5)

        # adjust offset again
        offset_val = os.measure(1)
        os.channel_offset(3, offset_val)
        sleep(0.5)

        # zoom in on oscillation again
        osc_val = float(os.measure(1)) / 4
        if osc_val < 5e-3:
            osc_val = 5e-3
        os.channel_scale(3, osc_val)
        sleep(1)

        # take oscope data
        osc_val = os.measure(3)
        offset_val = os.measure(1)
        # format freq,
        # print('freq: {:.0f} MHz; amp: {:.2f} dBm; offset: {:.1f} mV; osc amp: {.2f} mV'.format(
        #     freq_val / 1e6, amp_val, offset_val * 1e3, osc_val * 1e3
        # ))
        # record result
        dv.add(freq_val, offset_val, osc_val, context=cr)

except Exception as e:
    print('Error:', e)
