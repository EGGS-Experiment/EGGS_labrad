@REM: todo: rewrite, clean up, and make proper
@ECHO OFF
@SETLOCAL

@REM: todo either change prog_home or add scalabrad packages to this folder
SET CMD_LINE_ARGS=%*
SET PROG_HOME=%~dp0
SET JAVA_EXE="%JAVA_HOME%\bin\java.exe"

SET CMDLINE=%JAVA_EXE% -cp "%PROG_HOME%lib\*;" -Dprog.home="%PROG_HOME%..\bin" -Dprog.version="2.0.6" org.labrad.browser.WebServer %CMD_LINE_ARGS%
%CMDLINE%
@ENDLOCAL

EXIT /B
