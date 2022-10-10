"""
Characterize the frequency response of the RF locking system using an oscilloscope.
"""
import labrad
from time import sleep

from numpy import linspace, zeros
from EGGS_labrad.clients import createTrunk

script_name = "Frequency Response Characterization"
freq_range = linspace(0.1, 100, 1000) * 1e3
amp_range = (0.1, 0.2, 0.3, 0.4, 0.5)
os_channel = 3

osc_val = None
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    os = cxn.oscilloscope_server
    rf = cxn.rf_server
    fg = cxn.function_generator_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up oscilloscope
    os.select_device()
    os.measure_setup(2, os_channel, 'FREQ')
    os.measure_setup(3, os_channel, 'AMP')
    os.measure_setup(4, os_channel, 'MEAN')
    os.trigger_channel(os_channel)
    # os.trigger_level
    print("Oscilloscope setup successful.")

    # set up function generator
    fg.select_device()
    fg.amplitude(0.1)
    fg.function('SIN')
    fg.toggle(1)
    print("Function generator setup successful.")

    # set up signal generator
    rf.select_device()
    rf.amplitude(-12)
    rf.gpib_write("AM:E:D 100")
    rf.toggle(1)
    print("Signal generator setup successful.")

    # set up datavault
    trunk_tmp = createTrunk(script_name)
    dv.cd(trunk_tmp, True, context=cr)
    print("Dataset successfully created.")


    # SEQUENCE
    for amp_val in amp_range:
        # set modulation frequency
        fg.amplitude(amp_val)

        # set up dataset
        dv.new(
            'RF Frequency Response',
            [('RF Amplitude', 'dBm')],
            [('Frequency', 'Modulation Frequency', 'Hz'),
             ('Amplitude', 'Modulation Amplitude', 'V'),
             ('Mean', 'Signal Mean', 'V')],
            context=cr
        )

        for freq_val in freq_range:
            # set signal amplitude
            fg.frequency(freq_val)

            # first zoom out
            os.channel_offset(os_channel, 0)
            os.channel_scale(os_channel, 1)
            sleep(1)

            # center around offset
            offset_val = os.measure(4)
            os.channel_offset(os_channel, offset_val)
            sleep(1)

            # zoom in on oscillation
            osc_val = float(os.measure(3)) / 4
            if osc_val < 5e-3:
                osc_val = 5e-3
            elif osc_val > 1:
                sleep(1)
                osc_val = os.measure(3)
            os.channel_scale(os_channel, osc_val)
            sleep(1)

            # adjust offset again
            offset_val = os.measure(4)
            os.channel_offset(os_channel, offset_val)
            sleep(1)

            # zoom in on oscillation again
            osc_val = float(os.measure(3)) / 4
            if osc_val < 5e-3:
                osc_val = 5e-3
            elif osc_val > 1:
                sleep(1)
                osc_val = os.measure(3)
            os.channel_scale(os_channel, osc_val)
            sleep(2)

            # take oscope data
            freq_val = os.measure(2)
            amp_val = os.measure(3)
            mean_val = os.measure(4)

            # add to dataset
            dv.add([freq_val, freq_val, amp_val, mean_val], context=cr)


except Exception as e:
    print('Error:', e)
    print('osc val {}'.format(osc_val))
