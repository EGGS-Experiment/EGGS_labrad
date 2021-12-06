@ECHO OFF

::Starts all finished server

::Cryovac
START "Lakeshore Server" /min CMD "/k activate labart && python %LABRAD_ROOT%/servers/cryovac/lakeshore336_server.py"
START "NIOPS Server" /min CMD "/k activate labart && python %LABRAD_ROOT%/servers/cryovac/niops03_server.py"
START "Twistorr Server" /min CMD "/k activate labart && python %LABRAD_ROOT%/servers/cryovac/twistorr74_server.py"

::Trap
START "RF Server" /min CMD "/k activate labart && python %LABRAD_ROOT%/servers/trap/rf_server.py"

::ARTIQ
START "RF Server" /min CMD "/k activate labart && python %LABRAD_ROOT%/servers/ARTIQ/artiq_server.py"


activate labart
::CD "%LABRAD_ROOT%"