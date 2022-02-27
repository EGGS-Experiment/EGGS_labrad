::Starts all necessary LabRAD clients for monitoring

@ECHO OFF

START "RSG Client" /min CMD "/k activate grapher && python %HOME%\Code\RealSimpleGrapher\rsg_client.py"
::START "Script Scanner Client" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\clients\script_scanner_gui\script_scanner_gui.py"
::START "EGGS GUI" /min cmd "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\clients\EGGS_GUI\EGGS_GUI.py"