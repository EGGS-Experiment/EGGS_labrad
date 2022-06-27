:: Opens the RealSimpleGrapher Client.
::  Intended as a desktop shortcut.

@ECHO OFF

CD %EGGS_LABRAD_ROOT%\..\RealSimpleGrapher
CALL conda activate grapher
python rsg_client.py
