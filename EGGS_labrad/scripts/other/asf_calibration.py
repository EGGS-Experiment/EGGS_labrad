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
dds_frequency_hz = 110 * 1e6
dds_attenuation_dbm = 16
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
    sleep(0.5)
    aq.dds_attenuation(dds_channel, dds_attenuation_dbm)
    sleep(0.5)
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
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'ASF Calibration',
        [('ASF', 'Scale')],
        [('Power Meter Reading', 'Power', 'W')],
        context=cr
    )
    print('Dataset successfully created.')


    # MAIN SEQUENCE
    for amp_val in amp_range:
        # set asf
        aq.dds_amplitude(dds_channel, amp_val)
        sleep(0.25)

        # measure power
        res_pow = pm.measure()

        # record result
        print('asf {:f}: pow = {:f}'.format(amp_val, res_pow))
        dv.add(amp_val, res_pow, context=cr)

except Exception as e:
    print('Error:', e)
