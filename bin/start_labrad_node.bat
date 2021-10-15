@ECHO OFF

start "Labrad Web GUI" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
start "Labrad Node" /min cmd "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
start "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667