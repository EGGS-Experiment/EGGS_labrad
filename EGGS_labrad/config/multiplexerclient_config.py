class multiplexer_config(object):
    """
    Multiplexer client configuration file.
    Attributes
    ----------
    info: dict
    {
        channel_name: (port, hint, display_location, stretched, display_pid, dacPort, dac_rails)
    }
    """

    info = {
        # '397nm': (5, '461.251000', (0, 1), True, False, 3, [-4, 4], True),
        '423nm': (5, '709.07767', (0, 2), True, False, 0, [-4, 4], True),
        # '854nm': (5, '607.616000', (0, 2), True, False, 6, [-4, 4], True),
        # '866nm': (5, '607.616000', (0, 2), True, False, 6, [-4, 4], True),
    }

    ip = '10.97.111.8'
