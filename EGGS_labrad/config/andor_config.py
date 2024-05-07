class AndorConfig(object):
    """
    path to atmcd64d.dll SDK library
    """
    # SDK
    path_to_dll =       ('C:\\Users\\Elizabeth\\Documents\\Code\\Andor\\atmcd64d_legacy.dll')

    # temperature
    set_temperature =   -75 # degrees Celsius

    # acquisition setup
    read_mode =         'Image'
    acquisition_mode =  'Single Scan'
    trigger_mode =      'Internal'
    shutter_mode =      'Open'

    # readout setup
    emccd_gain =                    250
    exposure_time =                 0.100   # seconds
    binning =                       [1, 1]  # numbers of pixels for horizontal and vertical binning
    vertical_shift_amplitude =      0
    vertical_shift_speed =          0

    # image setup
    image_rotate =          "Anticlockwise"
    image_flip_horizontal = 1
    image_flip_vertical =   0

    # saving
    image_path =        ('C:\\Users\\Elizabeth\\Documents\\Code\\iXonImages')
    save_in_sub_dir =   True
    save_format =       "tsv"
    save_header =       True
