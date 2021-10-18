@ECHO OFF

START "Labrad Manager" /min %HOME%/Code/scalabrad-0.8.3/bin/labrad.bat --tls-required false
START "Labrad Web GUI" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667