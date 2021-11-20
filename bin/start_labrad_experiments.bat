@ECHO OFF

START "Labrad Data Vault" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/data_vault.py"
START "Labrad Parameter Vault" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/parameter_vault/parameter_vault.py"
START "Labrad Script Scanner" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/script_scanner/script_scanner.py"
START "Real Simple Grapher" /min CMD "/k activate labart && python %HOME%/Code/RealSimpleGrapher/rsg.py"