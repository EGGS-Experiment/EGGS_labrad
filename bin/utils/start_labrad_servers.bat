::Starts all finished LabRAD servers

CALL %EGGS_LABRAD_ROOT%\bin\prepare_labrad.bat

@REM: Cryovac
START "Lakeshore Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\lakeshore336_server.py"
START "NIOPS Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\niops03_server.py"
START "Twistorr Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\twistorr74_server.py"
START "RGA Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\rga_server.py"
REM START "FMA Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\cryovac\fma1700a_server.py"

@REM: Trap
START "RF Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\trap\rf_server.py"
START "DC Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\trap\dc_server.py"
START "AMO2 Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\AMO_boxes\AMO2_server.py"

@REM: Lasers
START "SLS Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\lasers\sls_server.py"
START "Toptica Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\lasers\toptica_server.py"

@REM: ARTIQ
START "ARTIQ Server" /min CMD "/k activate labart2 && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\ARTIQ\artiq_server.py"

@REM: Test & Measurement Devices
START "Oscilloscope Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\oscilloscopes\oscilloscope_server.py"
START "Function Generator Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\function_generators\functiongenerator_server.py"
START "Spectrum Analyzer Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\spectrum_analyzers\spectrumanalyzer_server.py"
START "Network Analyzer Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\network_analyzers\networkanalyzer_server.py"
START "Power Meter Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\power_meter\powermeter_server.py"
START "GPP3060 Server" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\power_supplies\GPP3060_server.py"
