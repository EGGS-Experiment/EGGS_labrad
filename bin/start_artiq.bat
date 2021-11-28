@ECHO OFF

::Starts all components necessary for running ARTIQ

start "ARTIQ Master" /min cmd "/k activate labart2 && artiq_master -g -r %ARTIQ_ROOT%/repository --device-db %ARTIQ_ROOT%/device_db.py --bind=192.168.1.28"
start "ARTIQ Dashboard" /min cmd "/k activate labart2 && artiq_dashboard"
start "ARTIQ Controller Manager" /min cmd "/k activate labart2 && artiq_ctlmgr"