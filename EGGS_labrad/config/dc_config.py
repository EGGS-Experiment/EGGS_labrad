class dc_config(object):
    """
    DC Client configuration file.
    Specifies which channels from the server to break out in the client
    and their layout.

    Attributes
    ----------
    row_length: int

    info: dict
    {
        channel_name: (num, row, col)
    }
    """
    row_length = 2

    channeldict = {
        'E Endcap':     {'num': 1, 'row': 1, 'col': 0},
        'W Endcap':     {'num': 2, 'row': 1, 'col': 1},
        'V Shim':       {'num': 3, 'row': 2, 'col': 0},
        'H Shim':       {'num': 4, 'row': 2, 'col': 1},
    }
