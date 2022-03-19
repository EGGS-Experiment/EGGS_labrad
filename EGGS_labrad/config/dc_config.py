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
        'Endcap 1':     {'num': 0, 'row': 1, 'col': 0},
        'Endcap 2':     {'num': 1, 'row': 1, 'col': 1},
        'Shim 1':       {'num': 2, 'row': 2, 'col': 0},
        'Shim 2':       {'num': 3, 'row': 2, 'col': 1},
        'Shim 3':       {'num': 4, 'row': 2, 'col': 3},
        'Shim 4':       {'num': 5, 'row': 2, 'col': 4},
    }
