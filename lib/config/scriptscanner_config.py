class config(object):

    #list in the format (import_path, class_name)
    scripts = [('EGGS_labrad.lib.scripts.experiments.vibration_measurement', 'vibration_measurement'),
               ('EGGS_labrad.lib.scripts.experiments.vibration_measurement_singleshot', 'vibration_measurement_ss'),
               ('EGGS_labrad.lib.scripts.experiments.test_experiment', 'test_experiment')
        ]

    allowed_concurrent = {
    }
    
    launch_history = 1000   
