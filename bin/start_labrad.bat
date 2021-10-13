@ECHO OFF

start /min cmd /c %HOME%/Code/EGGS_labrad/bin/start_labrad_core.bat
start /min cmd /c %HOME%/Code/EGGS_labrad/bin/start_labrad_devices.bat
start /min cmd /c %HOME%/Code/EGGS_labrad/bin/start_labrad_experiments.bat
start /min cmd /c %HOME%/Code/EGGS_labrad/bin/start_labrad_clients.bat
activate labart

PAUSE