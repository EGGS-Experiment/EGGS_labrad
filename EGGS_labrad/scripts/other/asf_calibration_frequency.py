"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
from time import sleep
from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'ASF Calibration'
dds_channel = 'urukul1_ch1'
dds_freq_range_mhz = linspace(70, 146, 20)
dds_attenuation_arr = (15, 16, 17, 18, 19)
amp_range = linspace(1, 50, 50) / 100

wav_nm = 400
num_avgs = 100


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    aq = cxn.artiq_server
    pm = cxn.power_meter_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up DDSs
    aq.dds_frequency(dds_channel, dds_frequency_hz)
    aq.dds_toggle(dds_channel, 1)
    print('DDS setup successful.')

    # set up power meter
    pm.select_device()
    pm.configure_wavelength(wav_nm)
    pm.configure_autoranging(1)
    pm.configure_mode('POW')
    pm.configure_averaging(num_avgs)
    print('Power meter setup successful.')

    # create dataset
    dep_vars = [
        ('{:f} dB'.format(att_dB), 'Attenuation', 'dB')
        for att_dB in dds_attenuation_arr
    ]
    dv.cd(createTrunk(name_tmp), True, context=cr)
    dv.new(
        'ASF Calibration - {:s}'.format(dds_channel),
        [('ASF', 'Scale')],
        dep_vars,
        context=cr
    )
    print('Dataset successfully created.')


    # MAIN SEQUENCE
    for amp_val in amp_range:
        # set asf
        aq.dds_amplitude(dds_channel, amp_val)

        # sweep attenuation
        pow_holder = [amp_val]
        for att_val in dds_attenuation_arr:
            # set att
            aq.dds_attenuation(dds_channel, att_val)
            sleep(0.1)

            # measure power
            pow_holder.append(pm.measure())

        # add data to dataset
        dv.add(pow_holder, context=cr)

except Exception as e:
    print('Error:', e)
