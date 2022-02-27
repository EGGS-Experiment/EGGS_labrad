::Starts all LabRAD servers needed for experiments

@ECHO OFF

REM: Servers
START "Labrad Data Vault" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\data_vault.py"
START "Labrad Parameter Vault" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\parameter_vault\parameter_vault.py"
START "Labrad Script Scanner" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\script_scanner\script_scanner.py"
