class AndorConfig(object):
    '''
    path to atmcd64d.dll SDK library
    thkim
    '''
    #default parameters
    path_to_dll = ('C:\\Program Files (x86)\\Andor SOLIS\\atmcd64d_legacy.dll')
    set_temperature = -20 #degrees C
    read_mode = 'Image'
    acquisition_mode = 'Single Scan'
    trigger_mode = 'Internal'
    exposure_time = 0.100 #seconds
    binning = [1, 1] #numbers of pixels for horizontal and vertical binning
    image_path = ('C:\\Users\\scientist\\Pictures\\iXonImages\\')
    save_in_sub_dir = True
    save_format = "tsv"
    save_header = True
