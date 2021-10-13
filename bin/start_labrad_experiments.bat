@ECHO OFF

::start "Labrad Data Vault" /min cmd "/k activate barium && python %HOME%/Code/servers/data_vault.py"
start "Labrad Data Vault" /min cmd "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/data_vault.py"
start "Labrad Parameter Vault" /min cmd "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/parameter_vault/parameter_vault.py"
start "Labrad Script Scanner" /min cmd "/k activate barium && python %HOME%/Code/EGGS_labrad/lib/servers/script_scanner/script_scanner.py"