::Starts all main LabRAD servers

::Prepare LabRAD CMD
CALL %LABRAD_ROOT%\bin\prepare_labrad.bat

::Core Servers
START "Labrad Manager" /min %HOME%\Code\scalabrad-0.8.3\bin\labrad.bat --tls-required false
START "Labrad Web GUI" /min %HOME%\Code\scalabrad-web-server-2.0.6\bin\labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

::Experiment Servers
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_experiments.bat

::Device Bus Servers
START "GPIB Device Manager" /min CMD "/k activate labart && python %LABRAD_ROOT%\lib\servers\gpib\gpib_device_manager.py"
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_devices.bat

::ARTIQ
START /min CMD /c %LABRAD_ROOT%\bin\start_artiq.bat

::Clients
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_clients.bat
