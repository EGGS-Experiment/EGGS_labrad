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
    shutter_mode =      'Auto'

    # readout setup
    exposure_time =     0.100   # seconds
    binning =           [1, 1]  # numbers of pixels for horizontal and vertical binning

    # image saving
    image_path =        ('C:\\Users\\Elizabeth\\Documents\\Code\\iXonImages')
    save_in_sub_dir =   True
    save_format =       "tsv"
    save_header =       True
