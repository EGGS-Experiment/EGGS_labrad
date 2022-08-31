"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
from time import sleep

from numpy import linspace, zeros, mean
from EGGS_labrad.clients import createTrunk

name_tmp = 'ASF Characterization'
(dds_channel_amp, dds_channel_power) = ('urukul0_ch1', 'urukul0_ch3')
dds_frequency_hz = 50 * 1e6
dds_attenuation_dbm = 10
amp_range = linspace(1, 100, 100) / 100
os_channel = 4
num_avgs = 10


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    aq = cxn.artiq_server
    os = cxn.oscilloscope_server
    sa = cxn.spectrum_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up DDSs
    for dds_name in (dds_channel_amp, dds_channel_power):
        # set frequency
        aq.dds_frequency(dds_name, dds_frequency_hz)
        sleep(0.5)
        # set attenuation
        aq.dds_attenuation(dds_name, dds_attenuation_dbm)
        sleep(0.5)
        # turn on
        aq.dds_toggle(dds_name, 1)
        sleep(0.5)

    # set up oscilloscope
    os.select_device()
    os.measure_setup(1, os_channel, 'AMP')
    os.measure_setup(2, os_channel, 'FREQ')
    # todo: turn off all channels except os channel
    os.trigger_channel(os_channel)
    os.trigger_level(os_channel, 0)

    # start centering oscope
    aq.dds_amplitude(dds_channel_amp, 0.1)
    os.autoscale()
    sleep(4)

    # vertical centering
    os.channel_probe(4, 1)
    amp_calib = os.measure(1)
    if (amp_calib < 20) and (amp_calib > 0):
        os.channel_scale(os_channel, amp_calib / 5)
    else:
        raise Exception('Bad reading: oscope amp')

    # horizontal centering
    time_calib = 1 / os.measure(2)
    if (time_calib > 3e-9) and (time_calib < 1):
        os.horizontal_scale(time_calib)
    else:
        print('time_calib: {f}'.format(time_calib))
        raise Exception('Bad reading: oscope freq')
    print('Oscilloscope setup successful.')

    # set up spectrum analyzer
    sa.select_device()
    sa.marker_toggle(1, True)
    print('Spectrum analyzer setup successful.')

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'ASF Characterization',
        [('ASF', 'Scale')],
        [('DDS Amplitude', 'Amplitude', 'V'), ('DDS Power', 'Power', 'dBm')],
        context=cr
    )
    print('Dataset successfully created.')


    # MAIN SEQUENCE
    for amp_val in amp_range:
        # set asf
        aq.dds_amplitude(dds_channel_amp, amp_val)
        aq.dds_amplitude(dds_channel_power, amp_val)

        # scale spec anal and oscope
        sa.autoset()

        # try to center oscope
        amp_calib = os.measure(1)
        if (amp_calib < 20) and (amp_calib > 0):
            os.channel_scale(os_channel, amp_calib / 5)
        else:
            raise Exception('Bad reading')

        # record oscope values
        os_amplitude = zeros(num_avgs)
        for i in range(num_avgs):
            os_amplitude[i] = os.measure(1)
            sleep(0.5)
        #print(os_amplitude)
        os_amplitude = mean(os_amplitude)

        # wait for spec anal to finish
        sleep(5)

        # get spec anal marker back and record
        sa.marker_toggle(1, 1)
        sleep(1)

        sa_power = zeros(num_avgs)
        for i in range(num_avgs):
            sa_power[i] = sa.marker_amplitude(1)
            sleep(0.5)

        sa_power = mean(sa_power)

        # record result
        print('asf {:f}: amp = {:f}, pow = {:f}'.format(amp_val, os_amplitude, sa_power))
        dv.add(amp_val, os_amplitude, sa_power, context=cr)

except Exception as e:
    print('Error:', e)
