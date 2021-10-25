@ECHO OFF

start "ARTIQ Master" /min cmd "/k activate labart2 && artiq_master -g -r %ARTIQ_ROOT%/repository --device-db %ARTIQ_ROOT%/device_db.py"
::start "ARTIQ Dashboard" /min cmd "/k activate labart2 && artiq_dashboard"
::start "ARTIQ Controller Manager" /min cmd "/k activate labart2 && artiq_ctlmgr"

::Submit pulser API to ARTIQ Master to be run
conda activate labart2 &&
artiq_client submit %HOME%/EGGS_labrad/lib/servers/pulser/pulser_api.py

PAUSE