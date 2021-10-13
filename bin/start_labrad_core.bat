@ECHO OFF

start "Labrad Manager" /min %HOME%/Code/scalabrad-0.8.3/bin/labrad.bat --tls-required false
start "Labrad Web Manager" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
start "Labrad Node" /min cmd "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
start "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://%LABRADHOST%:7667