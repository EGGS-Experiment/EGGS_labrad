try:
    name_tmp = 'RGA Single Trace'
    # connect to labrad
    import labrad
    cxn = labrad.connect()

    # general import
    from numpy import arange, transpose
    from EGGS_labrad.clients import createTrunk

    # get servers
    rga = cxn.rga_server
    dv = cxn.data_vault
    cr = cxn.context()

    # parameters
    (mass_initial, mass_final, mass_steps) = (1, 100, 10)
    dv_dep_var = [('Partial Pressures', 'Pressure', 'Torr')]

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(name_tmp, [('Atomic Mass', 'amu')], dv_dep_var, context=cr)

    # set up rga scan
    rga.scan_mass_initial(mass_initial)
    rga.scan_mass_final(mass_final)
    rga.scan_mass_steps(mass_steps)

    # turn on rga
    rga.ionizer_filament('*')

    # take rga data
    res = rga.scan_start('a', 1)
    res_t = transpose(res)
    # print(res)
    dv.add(res_t, context=cr)

except Exception as e:
    print('Error:', e)

finally:
    # turn off rga
    rga.ionizer_filament(0)
