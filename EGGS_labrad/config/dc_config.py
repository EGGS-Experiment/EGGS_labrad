class dcConfig(object):
    """
    DC Client configuration file.
    Specifies which channels from the server to break out in the client
    and their layout.

    Attributes
    ----------
    info: dict
    {
        channel_name: (num, row, col)
    }
    """

    channeldict = {
        'Endcap 1': {'num': 0, 'row': 1, 'col': 1},
        'Endcap 2': {'num': 1, 'row': 1, 'col': 2}
        'Shim 1': {'num': 2, 'row': 2, 'col': 0},
        'Shim 2': {'num': 3, 'row': 2, 'col': 1},
    }
