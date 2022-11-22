"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
from time import sleep
from numpy import arange, linspace, zeros, mean, amax

from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'ASF Characterization'
(dds_channel_amp, dds_channel_power) = ('urukul0_ch2', 'urukul0_ch3')
num_avgs = 10

# dds parameters
dds_freq_hz = 110 * 1e6
dds_att_list_dbm = arange(5, 11)
dds_amp_list_pct = linspace(1, 100, 100) / 100

# device parameters
os_channel = 3


try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    aq = cxn.artiq_server
    os = cxn.oscilloscope_server
    sa = cxn.spectrum_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # check DDS attenuation values are valid
    if amax(dds_att_list_dbm) < 2:
        raise Exception("Error: value in dds attenuation list is too high.")

    # set up DDSs
    for dds_name in (dds_channel_amp, dds_channel_power):
        # turn on DDS
        aq.dds_toggle(dds_name, 1)
        # set amplitude
        aq.dds_frequency(dds_channel_amp, dds_freq_hz)

    # set up oscilloscope
    os.select_device(2)
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
        raise Exception("Bad reading: oscope amp")

    # horizontal centering
    os.horizontal_scale(1 / dds_freq_hz)
    print("Oscilloscope setup successful.")

    # set up spectrum analyzer
    sa.select_device()
    sa.marker_toggle(1, True)
    print("Spectrum analyzer setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Data vault successfully setup.")

    # sweep attenuation
    for att_val in dds_att_list_dbm:

        # create dataset
        dataset_title_tmp = 'ASF Characterization: {} dB'.format(str(att_val).replace('.', '_'))
        dv.new(
            dataset_title_tmp,
            [('ASF', 'Scale')],
            [('DDS Amplitude', 'Amplitude', 'V'), ('DDS Power', 'Power', 'dBm')],
            context=cr
        )
        dv.add_parameter("attenuation", att_val, context=cr)

        # set attenuation
        aq.dds_attenuation(dds_channel_amp, att_val)
        aq.dds_attenuation(dds_channel_power, att_val)

        # sweep asf
        for amp_val in dds_amp_list_pct:

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
                raise Exception("Bad reading")

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
            print("asf {:f}: amp = {:f}, pow = {:f}".format(amp_val, os_amplitude, sa_power))
            dv.add(amp_val, os_amplitude, sa_power, context=cr)

except Exception as e:
    print("Error:", e)
    cxn.disconnect()
