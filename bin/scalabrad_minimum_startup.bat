@echo off

SET ERROR_CODE=0
@setlocal

SET JAVA_EXE="%JAVA_HOME%\bin\java.exe"
SET CMD_LINE_ARGS=%*
SET PROG_HOME=%~dp0..

SET CMDLINE=%JAVA_EXE%  -cp "%PROG_HOME%\lib\*;" -Dprog.home="%PROG_HOME%" -Dprog.version="0.8.3" org.labrad.manager.Manager %CMD_LINE_ARGS%
%CMDLINE%

@endlocal
if ERRORLEVEL 1 (set ERROR_CODE=1)

exit /B %ERROR_CODE%
