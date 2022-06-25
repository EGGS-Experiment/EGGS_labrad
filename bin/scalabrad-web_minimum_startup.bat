@ECHO OFF
@SETLOCAL

REM: todo either change prog_home or add scalabrad packages to this folder
SET CMD_LINE_ARGS=%*
SET PROG_HOME=%~dp0..

"%JAVA_HOME%\bin\java.exe" -cp "%PROG_HOME%\lib\*;" -Dprog.home="%PROG_HOME%" -Dprog.version="2.0.6" org.labrad.browser.WebServer %CMD_LINE_ARGS%

@ENDLOCAL

EXIT /B
