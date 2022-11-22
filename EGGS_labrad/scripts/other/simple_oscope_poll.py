import labrad
from time import sleep

from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization'
os_channel = 3

osc_val = None
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    os = cxn.oscilloscope_server
    rf = cxn.rf_server
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

    # set up signal generator
    rf.select_device()
    rf.gpib_write("AM OFF")
    print("Signal generator setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Dataset successfully created")

        # create dataset
    dv.new(
        'Oscope Poll {:d} kHz'.format(int(freq_val / 1e3)),
        [('RF Amplitude', 'dBm')],
        [('Rectifier Offset', 'DC Offset', 'V'), ('Rectifier Value', 'Oscillation Amplitude', 'V')],
        context=cr
        )


    # take oscope data
    osc_val = os.measure(3)
    offset_val = os.measure(4)
     # format freq,
    # print('freq: {:.0f} MHz; amp: {:.2f} dBm; offset: {:.1f} mV; osc amp: {.2f} mV'.format(
    #     freq_val / 1e6, amp_val, offset_val * 1e3, osc_val * 1e3
    # ))
    # record result
    dv.add(osc_val, context=cr)

except Exception as e:
    print('Error:', e)
    print('osc val {}'.format(osc_val))
