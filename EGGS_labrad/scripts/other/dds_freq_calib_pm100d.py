"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
from time import sleep
from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'Laser Power Scan'
dds_channel = 'urukul0_ch1'
dds_frequency_hz_list = linspace(103, 106, 301) * 1e6
dds_amp_pct = 50
dds_att_db = 8

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
    aq.dds_amplitude(dds_channel, dds_amp_pct / 100)
    aq.dds_attenuation(dds_channel, dds_att_db)
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
    dv.cd(createTrunk(name_tmp), True, context=cr)
    dv.new(
        'ASF Calibration - {:s}'.format(dds_channel),
        [('Frequency', 'MHz')],
        [('Laser Power', 'Power', 'mW')],
        context=cr
    )
    print('Dataset successfully created.')


    # MAIN SEQUENCE
    for freq_val_hz in dds_frequency_hz_list:
        # set asf
        aq.dds_frequency(dds_channel, freq_val_hz)
        sleep(0.25)

        # get power reading
        pow_mw = pm.measure()

        # add data to dataset
        dv.add([freq_val_hz / 1e6, pow_mw], context=cr)

except Exception as e:
    print('Error:', e)
