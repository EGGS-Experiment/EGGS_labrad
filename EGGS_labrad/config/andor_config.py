class AndorConfig(object):
    '''
    path to atmcd64d.dll SDK library
    '''
<<<<<<< HEAD
    #default parameters
    path_to_dll = ('C:\\Program Files\\Andor SOLIS\\atmcd64d_legacy.dll')
    #path_to_dll = ('C:\\Users\\spectroscopy\\Documents\\Code\\Andor\\atmcd64d_legacy.dll')
    set_temperature = -20 #degrees C
=======
    # default parameters
    path_to_dll = ('C:\\Users\\Elizabeth\\Documents\\Code\\Andor\\atmcd64d_legacy.dll')
    set_temperature = -20 # degrees C
>>>>>>> 1ada6817f5b9620c23aa558d6c19dd957aea03c5
    read_mode = 'Image'
    acquisition_mode = 'Single Scan'
    trigger_mode = 'Internal'
    exposure_time = 0.100 # seconds
    binning = [1, 1] # numbers of pixels for horizontal and vertical binning
    image_path = ('C:\\Users\\Elizabeth\\Documents\\Code\\iXonImages')
    save_in_sub_dir = True
    save_format = "tsv"
    save_header = True
