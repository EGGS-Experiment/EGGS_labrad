@ECHO OFF
@SETLOCAL

SET CMD_LINE_ARGS=%*
SET PROG_HOME=%~dp0
SET JAVA_EXE="%JAVA_HOME%\bin\java.exe"

SET CMDLINE=%JAVA_EXE% -cp "%PROG_HOME%lib\*;" -Dprog.home="%PROG_HOME%..\bin" -Dprog.version="0.8.3" org.labrad.manager.Manager %CMD_LINE_ARGS%
%CMDLINE%

@ENDLOCAL

EXIT /B
