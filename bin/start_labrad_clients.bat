@ECHO OFF

start "Real Simple Grapher" /min cmd "/k activate labart && TIMEOUT 3 && python %HOME%/Code/RealSimpleGrapher/rsg.py"
start "Script Scanner Client" /min cmd "/k activate labart && TIMEOUT 3 && python %HOME%/Code\EGGS_labrad\lib\clients\script_scanner_gui\script_scanner_gui.py"
::start "EGGS Client" /min cmd "/k activate labart && TIMEOUT 3 && python %HOME%/Code\EGGS_labrad\lib\clients\lakeshore_client\lakeshore_client.py"
::start "EGGS Client" /min cmd "/k activate labart && TIMEOUT 3 && python %HOME%/Code\EGGS_labrad\lib\clients\EGGS_GUI\EGGS_GUI.py"