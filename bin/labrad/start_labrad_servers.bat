::Starts all finished LabRAD servers

CALL %LABRAD_ROOT%\bin\prepare_labrad.bat

REM: Cryovac
START "Lakeshore Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\cryovac\lakeshore336_server.py"
START "NIOPS Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\cryovac\niops03_server.py"
START "Twistorr Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\cryovac\twistorr74_server.py"
START "RGA Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\cryovac\rga_server.py"

REM: Trap
START "RF Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\trap\rf_server.py"

REM: Lasers
START "SLS Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\lasers\sls_server.py"

REM: ARTIQ
START "ARTIQ Server" /min CMD "/k activate labart2 && python %LABRAD_ROOT%\lib\servers\ARTIQ\artiq_server.py"

REM: Imaging
START "PMT Server" /min CMD "/k activate labart2 && python %LABRAD_ROOT%\lib\servers\pmt\pmt_server.py"

