#!/usr/bin/env python3
"""
ARTIQ Start - RDX
Starts all components necessary for running ARTIQ via configuration file (artiq_config.py).
artiq_config.py needs to be in the same directory as this file.
"""
import os
import sys
import subprocess
from importlib import import_module
# from importlib.util import spec_from_file_location, module_from_spec


def main():
    # get artiq_config dict to configure master/ctlmgr/dashboard
    # assume artiq_config.py is in same directory as this file
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'artiq_config.py'
    )
    # print('idk: \t', sys.argv[0])

    # get configuration dict from artiq_config.py
    # spec = spec_from_file_location("module.name", "/path/to/file.py")
    # foo = module_from_spec(spec)
    # sys.modules["module.name"] = foo
    # spec.loader.exec_module(foo)
    # foo.MyClass()
    # artiq_config = import_module(config_path, 'artiq_config')
    # artiq_config = import_module('config_dict', '.artiq_config')
    _artiq_config = import_module('artiq_config', 'config_dict')
    artiq_config = _artiq_config.config_dict

    # process artiq config
    # master_args = [
    #     '--{:s} {:s}'.format(*arg)
    #     for arg in artiq_config['master_args']
    # ]
    # ctlmgr_args = [
    #     '--{:s} {:s}'.format(*arg)
    #     for arg in artiq_config['ctlmgr_args']
    # ]
    # dashboard_args = [
    #     '--{:s} {:s}'.format(*arg)
    #     for arg in artiq_config['dashboard_args']
    # ]

    # master_args = [
    #     arg_cmd
    #     for arg in artiq_config['master_args']
    #     for arg_cmd in ('--{:s}'.format(arg[0]), arg[1])
    # ]

    master_args = [
        arg_cmd
        for arg in artiq_config['master_args']
        for arg_cmd in arg
    ]
    ctlmgr_args = [
        arg_cmd
        for arg in artiq_config['master_args']
        for arg_cmd in arg
    ]
    dashboard_args = [
        arg_cmd
        for arg in artiq_config['master_args']
        for arg_cmd in arg
    ]
    print(master_args)

    # prepare execution strings
    master_cmd    = [sys.executable, "-u", "-m", "artiq.frontend.artiq_master"] + master_args
    dashboard_cmd = [sys.executable,       "-m", "artiq.frontend.artiq_dashboard"] + dashboard_args
    ctlmgr_cmd    = [sys.executable,       "-m", "artiq_comtools.artiq_ctlmgr"] + ctlmgr_args

    # create master subprocess
    with subprocess.Popen(master_cmd,
                          stdout=subprocess.PIPE, universal_newlines=True,
                          bufsize=1) as master:
        master_ready = False

        # forward master stdout
        for line in iter(master.stdout.readline, ""):
            sys.stdout.write(line)
            if line.rstrip() == "ARTIQ master is now ready.":
                master_ready = True
                break

        # start clients/servers only after master has started
        if master_ready:
            with subprocess.Popen(dashboard_cmd):
                with subprocess.Popen(ctlmgr_cmd):
                    for line in iter(master.stdout.readline, ""):
                        sys.stdout.write(line)
        else:
            print("artiq_start_rdx: master failed to start, exiting.")


if __name__ == "__main__":
    main()
