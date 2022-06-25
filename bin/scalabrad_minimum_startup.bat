@ECHO OFF
@SETLOCAL

SET CMD_LINE_ARGS=%*
SET PROG_HOME=%~dp0..

"%JAVA_HOME%\bin\java.exe" -cp "%PROG_HOME%\lib\*;" -Dprog.home="%PROG_HOME%" -Dprog.version="0.8.3" org.labrad.manager.Manager %CMD_LINE_ARGS%

@ENDLOCAL

EXIT /B
