::Starts all finished LabRAD servers

CALL %EGGS_LABRAD_ROOT%\bin\prepare_labrad.bat

REM: Cryovac
START "Lakeshore Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\lakeshore336_server.py"
START "NIOPS Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\niops03_server.py"
START "Twistorr Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\twistorr74_server.py"
START "RGA Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\rga_server.py"
START "FMA Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\fma1700a_server.py"

REM: Trap
START "RF Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\trap\rf_server.py"
START "DC Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\trap\dc_server.py"

REM: Lasers
START "SLS Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\lasers\sls_server.py"

REM: ARTIQ
START "ARTIQ Server" /min CMD "/k activate labart2 && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\ARTIQ\artiq_server.py"

REM: Imaging
START "PMT Server" /min CMD "/k activate labart2 && TIMEOUT 2 && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\pmt\pmt_server.py"

