"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
import numpy as np

from time import sleep
from numpy import arange, linspace, zeros, mean, amax

from EGGS_labrad.clients import createTrunk

# experiment parameters
name_tmp = 'EGGS Characterization TMP'
dds_channel = 'urukul0_ch2'
num_avgs = 5

# dds parameters
dds_att_db = 31.5
dds_freq_list_hz = arange(69, 95, .01) * 1e6
#dds_amp_list_pct = linspace(1, 100, 100) / 100
dds_amp_list_pct = np.array([0.5])

# device parameters
os_channel = 3


try:
    # connect to labrad
    cxn = labrad.connect()
    print("Connection successful.")

    # get servers
    aq = cxn.artiq_server
    os = cxn.oscilloscope_server
    dv = cxn.data_vault
    cr = cxn.context()
    print("Server connection successful.")

    # set up oscilloscope
    os.select_device(0)
    os.measure_setup(1, os_channel, 'AMP')
    os.measure_setup(2, os_channel, 'MEAN')
    # todo: turn off all channels except os channel
    #os.trigger_channel(os_channel)
    #os.trigger_level(os_channel, 0)

    # start centering oscope
    aq.dds_toggle(dds_channel, 1)
    aq.dds_attenuation(dds_channel, dds_att_db)
    os.autoscale()
    sleep(5)

    # vertical centering
    #os.channel_probe(4, 1)
    amp_calib = os.measure(1)
    if (amp_calib < 20) and (amp_calib > 0):
        os.channel_scale(os_channel, amp_calib / 5)
    else:
        raise Exception("Bad reading: oscope amp")

    print("Oscilloscope setup successful.")

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    print("Data vault successfully setup.")

    # sweep amplitude
    for amp_val in dds_amp_list_pct:

        # create dataset
        dataset_title_tmp = 'EGGS Characterization: {} asf'.format(str(amp_val).replace('.', '_'))
        dv.new(
            dataset_title_tmp,
            [('Frequency', 'Hz')],
            [('Mean Amplitude', 'Amplitude', 'V'), ('Mean Voltage', 'Voltage', 'V')],
            context=cr
        )
        dv.add_parameter("amplitude", amp_val, context=cr)
        dv.add_parameter("samples", num_avgs, context=cr)

        # set amplitude
        aq.dds_amplitude(dds_channel, amp_val)

        # tmp
        sleep(6)

        # sweep frequency
        for freq_val in dds_freq_list_hz:

            # set frequencuy
            aq.dds_frequency(dds_channel, freq_val)

            # try to center oscope
            amp_calib = os.measure(1)
            if (amp_calib < 20) and (amp_calib > 0):
                os.channel_scale(os_channel, amp_calib / 5)
            else:
                raise Exception("Bad reading")

            # horizontal centering
            os.horizontal_scale(1 / freq_val)

            # record oscope values
            os_amplitude = zeros(num_avgs)
            os_mean = zeros(num_avgs)
            for i in range(num_avgs):
                os_amplitude[i] = os.measure(1)
                sleep(0.2)
                os_mean[i] = os.measure(2)

            #print(os_amplitude)
            os_amplitude = mean(os_amplitude)
            os_mean = mean(os_mean)

            # record result
            #print("\tfreq {:f} MHz: ampl = {:f}, mean = {:f}".format(freq_val / 1e6, os_amplitude, os_mean))
            print("\t{:f},{:f},{:f}".format(freq_val / 1e6, os_amplitude, os_mean))
            dv.add(freq_val, os_amplitude, os_mean, context=cr)

except Exception as e:
    print("Error: {}".format(e))
    cxn.disconnect()
