class multiplexer_config(object):
    """
    Multiplexer client configuration file.
    Attributes
    ----------
    info: dict
    {
        channel_name: (port, frequency, display_location, stretched, display_pid, dacPort, dac_rails)
    }
    """

    info = {
        # '397nm': (5, '461.251000', (0, 1), True, False, 4, [-4, 4], True),
        '423nm': (6, '709.07767', (0, 2), True, False, 5, [-4, 4], True),
        '854nm': (13, '607.616000', (0, 3), True, False, 12, [-4, 4], True)
        # '866nm': (14, '607.616000', (0, 4), True, False, 13, [-4, 4], True),
    }

    ip = '10.97.111.8'
