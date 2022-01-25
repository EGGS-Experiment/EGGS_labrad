class dcConfig(object):
    """
    Specifies the hardware configuration for the AMO8 server.
    """

    rowLength = 5

    channeldict = {
        'group1': {
            'Endcap 1': {'num': 0, 'row': 1, 'col': 1},
            'Endcap 2': {'num': 1, 'row': 1, 'col': 2}
        },

        'row2': {
            'Shim 1': {'num': 2, 'row': 2, 'col': 0},
            'Shim 2': {'num': 3, 'row': 2, 'col': 1},
            'Shim 3': {'num': 4, 'row': 2, 'col': 2},
            'Shim 4': {'num': 5, 'row': 2, 'col': 3}
        }
    }