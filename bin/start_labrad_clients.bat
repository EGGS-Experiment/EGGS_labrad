@ECHO OFF

::Starts all necessary clients for the lab

START "Real Simple Grapher" /min CMD "/k activate labart && TIMEOUT 3 && python %HOME%/Code/RealSimpleGrapher/rsg.py"
START "Script Scanner Client" /min CMD "/k activate labart && TIMEOUT 3 && python %HOME%/Code\EGGS_labrad\lib\clients\script_scanner_gui\script_scanner_gui.py"
START "EGGS Client" /min cmd "/k activate labart && TIMEOUT 2 && python %HOME%/Code\EGGS_labrad\lib\clients\lakeshore_client\lakeshore_client.py"
::start "EGGS Client" /min cmd "/k activate labart && TIMEOUT 2 && python %HOME%/Code\EGGS_labrad\lib\clients\EGGS_GUI\EGGS_GUI.py"