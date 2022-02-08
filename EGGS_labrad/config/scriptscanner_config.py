"""
Script Scanner config object.
Specifies the scripts available to script scanner on startup.
"""
class config(object):

    # list in the format (import_path, class_name)
    scripts = [('EGGS_labrad.scripts.experiments.vibration_measurement', 'vibration_measurement'),
               ('EGGS_labrad.scripts.experiments.vibration_measurement_singleshot', 'vibration_measurement_ss'),
               ('EGGS_labrad.scripts.experiments.test_experiment', 'test_experiment'),
               ('EGGS_labrad.scripts.experiments.sample_experiment', 'conflicting_experiment')
        ]

    allowed_concurrent = {
    }
    
    launch_history = 1000
