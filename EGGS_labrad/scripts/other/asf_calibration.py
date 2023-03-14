"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
from time import sleep
from numpy import array, arange, linspace
from EGGS_labrad.clients import createTrunk

name_tmp =                      'ASF Calibration'

dds_channel =                   'urukul0_ch1'
dds_frequency_hz =              103.7725 * 1e6
dds_attenuation_arr =           arange(8, 31.5, 0.5)
# amp_range = linspace(1, 50, 50) / 100

pm_wavelength_nm =              729
pm_num_avgs =                   100


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
    pm.configure_wavelength(pm_wavelength_nm)
    pm.configure_autoranging(1)
    pm.configure_mode('POW')
    pm.configure_averaging(pm_num_avgs)
    print('Power meter setup successful.')

    # create dataset
    dv.cd(createTrunk(name_tmp), True, context=cr)
    dv.new(
        'DDS Attenuation Calibration - {:s}'.format(dds_channel),
        [('Attenuation', 'dB')],
        [('Power', 'Power', 'mW')],
        context=cr
    )
    print('Dataset successfully created.')


    # MAIN SEQUENCE
    for att_val in dds_attenuation_arr:

        # set attenuation
        aq.dds_attenuation(dds_channel, att_val)
        sleep(0.1)

        # add data to dataset
        dv.add([att_val, pm.measure()], context=cr)

except Exception as e:
    print('Error:', e)
