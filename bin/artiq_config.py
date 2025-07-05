#!/usr/bin/env python3
"""
Configuration file for the experiment's ARTIQ system.
Used for simpler/easier startup (vs entering everything each time lol)
"""
from time import strftime, localtime

# todo: artiq-master --log-submissions - log experiment submissions to specified file
config_dict = {
    # arguments for artiq_master
    'master_args': [
        # display name for artiq_master
        ('name', 'EGGS1_ARTIQ_MASTER'),
        # additional hostname or IP address to bind to; use ‘*’ to bind to all interfaces (default: [])
        ('bind', '*'),
        # use git repository backend
        ('git', ''),
        # logging verbosity level: 'verbose' to increase, 'quiet' to decrease (default is WARNING)
        ('verbose', ''),
        ('verbose', ''),

        # path to experiment repository
        ('repository', 'C:\\Users\\EGGS1\\Documents\\Code\\artiq-master\\repository'),
        # path to subdirectory that contains actual experiments (must be subdir of path_repository)
        ('experiment-subdbdir', 'experiments'),
        # path to device_db.py file
        ('device-db', 'C:\\Users\\EGGS1\\Documents\\Code\\artiq-master\\LAX_exp\\device-db.py'),
        # path to dataset_db.mdb file
        ('dataset-db', 'C:\\Users\\EGGS1\\Documents\\Code\\artiq-master\\dataset_db.mdb'),
        # path to logfile
        ('log-file', 'C:\\Users\\EGGS1\\Documents\\.labrad\\logfiles\\artiq\\{:s}'.format(
            strftime("%Y_%m_%d__%H_%M_%S.log", localtime())
        )),
    ],

    # arguments for artiq_ctlmgr
    'ctlmgr_args': [
        # IP address of controllers to launch (local address of master connection by default)
        ('host-filter', '192.168.1.48'),
        # additional hostname or IP address to bind to; use ‘*’ to bind to all interfaces (default: [])
        ('bind', '*'),
        # IP address of the master; used by artiq_ctlmgr and artiq_dashboard
        ('server', '192.168.1.48'),
    ],

    # arguments for artiq_dashboard
    'dashboard_args': [
        # IP address of the master; used by artiq_ctlmgr and artiq_dashboard
        ('server', '192.168.1.48'),
    ],
}

