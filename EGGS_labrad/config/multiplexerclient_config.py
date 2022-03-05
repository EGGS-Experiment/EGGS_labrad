class multiplexer_config(object):
    '''
    multiplexer client configuration file
    
    Attributes
    ----------
    info: dict
    {
        channel_name: (port, hint, display_location, stretched, display_pid, dac, dac_rails))
    }
    '''
    info = {
        'Laser 1': (3, '461.251000', (0, 1), True, False, 3, [-4, 4], True),
        'Laser 2': (2, '607.616000', (0, 2), True, False, 6, [-4, 4], True),
    }

    ip = '10.97.111.8'
