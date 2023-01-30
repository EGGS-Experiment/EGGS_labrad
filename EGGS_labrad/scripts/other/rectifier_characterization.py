"""
Characterize the rectifier for PID stabilization of the trap RF via oscilloscope.
"""
# todo: make a proper experiment
# todo: make messages correct
import labrad
from time import sleep

from numpy import linspace, arange, array
from EGGS_labrad.clients import createTrunk

name_tmp = 'Rectifier Characterization'


# polling parameters
poll_delay_s =          0.75

# function generator parameters
fg_device_num_dj =      4
fg_freq_hz_list =       arange(5, 35, 5) * 1e6
fg_ampl_v_list =        arange(0.1, 5, 0.1)

# oscilloscope parameters
os_device_num_dj =      2
os_chan_num =           1


# main loop
try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    os = cxn.oscilloscope_server
    fg = cxn.function_generator_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up oscilloscope
    os.select_device(os_device_num_dj)
    os.measure_setup(1, os_chan_num, 'MAX')
    os.measure_setup(2, os_chan_num, 'MIN')
    os.measure_setup(3, os_chan_num, 'AMP')
    os.measure_setup(4, os_chan_num, 'MEAN')
    os.trigger_channel(os_chan_num)
    # os.trigger_level
    print("Oscilloscope setup successful.")

    # set up function generator
    fg.select_device(fg_device_num_dj)
    fg.toggle(True)
    fg.gpib_write('OUTP:IMP INF')
    print("Function generator setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Dataset successfully created")

    for freq_val in fg_freq_hz_list:
        # set signal frequency
        fg.frequency(freq_val)

        # todo: correctly set timescale

        # create dataset
        dv.new(
            'Rectifier Response {:d} kHz'.format(int(freq_val / 1e3)),
            [('Signal Amplitude', 'Vpp')],
            [
                ('Rectifier Offset',    'DC Offset',                'V'),
                ('Rectifier Value',     'Oscillation Amplitude',    'Vpp')
            ],
            context=cr
        )
        dv.add_parameter("function_generator_frequency_hz", freq_val, context=cr)
        # todo: add parameters

        for amp_val in fg_ampl_v_list:
            # set signal amplitude
            fg.amplitude(amp_val)

            # first zoom out
            os.channel_offset(os_chan_num, 0)
            os.channel_scale(os_chan_num, 1)
            sleep(0.5)

            # center around offset
            offset_val = os.measure(4)
            os.channel_offset(os_chan_num, offset_val)
            sleep(0.5)

            # zoom in on oscillation
            max_val = os.measure(1)
            min_val = os.measure(2)
            _signal_range = max_val - min_val
            os.channel_scale(os_chan_num, _signal_range)
            sleep(0.5)

            # adjust offset again
            offset_val = os.measure(4)
            os.channel_offset(os_chan_num, offset_val)
            sleep(0.5)

            # zoom in on oscillation again
            max_val = os.measure(1)
            min_val = os.measure(2)
            _signal_range = (max_val - min_val)
            os.channel_scale(os_chan_num, _signal_range)
            sleep(0.5)

            # adjust offset again
            _offset_val_tmp = os.measure(4)
            if _offset_val_tmp > 1e37:
                os.channel_offset(os_chan_num, offset_val)
            else:
                os.channel_offset(os_chan_num, _offset_val_tmp)

            # take oscope data
            osc_val = os.measure(3)
            offset_val = os.measure(4)
            if osc_val > 1e37:
                osc_val = 0
            # format freq,
            print('freq: {:.0f} MHz; amp: {:.2f} Vpp; offset: {:.1f} mV; osc amp: {:.2f} mV'.format(
                freq_val / 1e6, amp_val, offset_val * 1e3, osc_val * 1e3
            ))
            # record result
            dv.add(amp_val, offset_val, osc_val, context=cr)

except Exception as e:
    print('Error:', e)
    print('osc val {}'.format(osc_val))
